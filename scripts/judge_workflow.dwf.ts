interface BatchOutcome {
  /** 实际写入判定 JSON 的对象数。 */
  written: number;
  /** 该批首个对象 id。 */
  first: string;
  /** 该批末个对象 id。 */
  last: string;
}

const DIR = "D:\\harness office\\research\\jobtask-agent\\out\\judge_input";
const OUTDIR = "D:\\harness office\\research\\jobtask-agent\\out\\judge_output";

const batches: string[] = [];
for (let i = 0; i < 34; i += 1) batches.push(`g1_batch_${String(i).padStart(3, "0")}`);
for (let i = 0; i < 26; i += 1) batches.push(`g2_batch_${String(i).padStart(3, "0")}`);
for (let i = 0; i < 6; i += 1) batches.push(`g3_batch_${String(i).padStart(3, "0")}`);

const SYS =
  "你是组织经济学预测 agent 的前因判定员，为岗位—任务网络上的三再捆绑准则做前因判定。" +
  "你严格按批次文件头部的判定协议逐对象判定，不引入文件之外的信息，不编造 id。" +
  "如果批次文件读不到、格式和协议描述不符、或任务自相矛盾，如实说明并返回 written=0，而不是猜一个结果。";

const askText = (b: string, retryNote: string) =>
  `${retryNote}用 Read 工具读取批次文件 ${DIR}\\${b}.txt（头部是判定协议，正文是逐个对象块）。\n` +
  `逐个对象按协议判定三个字段：\n` +
  `- holds：前因是否成立，0 或 1；\n` +
  `- p：该对象未来发生协议所述后果的概率档位，只取 0.05/0.1/0.2/0.3/0.5/0.7/0.9 之一；\n` +
  `- why：≤30 字中文依据。\n` +
  `判定完成后，用 Write 工具把严格 JSON 数组写入 ${OUTDIR}\\${b}.json（UTF-8）：每个对象一个元素，顺序与文件中的对象块一致，字段名为 id/holds/p/why，id 照抄对象块第一行方括号里 id= 后面的值。\n` +
  `写完文件后，回复只含一个 JSON 对象：{"written": <实际写入的对象数>, "first": "<首个id>", "last": "<末个id>"}。不要在回复里输出判定数组全文，不要修改输入文件。`;

phase("LLM 逐对象判定三准则前因");
log(`共 ${batches.length} 批（准则一 34、准则二 26、准则三 6），每批最多 60 个对象`);
let okCount = 0;
const outcomes: { batch: string; written: number; status: string }[] = [];
await Promise.all(
  batches.map(async (b) => {
    const judge = agent(`判定员-${b}`, { system: SYS });
    try {
      const r = await judge.ask<BatchOutcome>(askText(b, ""));
      const status = r.written > 0 ? "ok" : "empty";
      if (status === "ok") okCount += 1;
      report({ batch: b, written: r.written, status });
      outcomes.push({ batch: b, written: r.written, status });
    } catch {
      report({ batch: b, written: 0, status: "failed" });
      outcomes.push({ batch: b, written: 0, status: "failed" });
    }
  }),
);

phase("补标失败批次");
const failed = outcomes.filter((o) => o.status !== "ok");
log(`${outcomes.length - failed.length} 批成功，${failed.length} 批需要补标`);
const retried: string[] = [];
for (const f of failed) {
  const judge = agent(`补标员-${f.batch}`, { system: SYS });
  try {
    const r = await judge.ask<BatchOutcome>(
      askText(f.batch, `上一次判定没有成功落盘（状态 ${f.status}）。请重新完整执行一遍。\n`),
    );
    if (r.written > 0) {
      okCount += 1;
      retried.push(f.batch);
      report({ batch: f.batch, written: r.written, status: "ok-retry" });
    } else {
      report({ batch: f.batch, written: 0, status: "failed-retry" });
    }
  } catch {
    report({ batch: f.batch, written: 0, status: "failed-retry" });
  }
}

phase("汇总判定进度");
const stillBad = failed.filter((f) => !retried.includes(f.batch)).map((f) => f.batch);
await artifact.markdown(
  "summary",
  [
    `# 三准则前因判定进度`,
    "",
    `- 计划批次 ${batches.length} 批，成功落盘 ${okCount} 批（含补标 ${retried.length} 批）。`,
    `- 仍未落盘：${stillBad.length === 0 ? "无" : stillBad.join(", ")}`,
    `- 结果目录：out/judge_output/（每批一个 JSON 数组，字段 id/holds/p/why）`,
  ].join("\n"),
  { title: "前因判定落盘清单", description: "66 批 LLM 前因判定的完成情况。" },
);

return {
  conclusion: `三准则前因判定：${batches.length} 批中 ${okCount} 批成功落盘到 out/judge_output/，${stillBad.length} 批失败（${stillBad.join(", ") || "无"}）。`,
  verified: ["每批由独立子代理判定并写入 JSON，written>0 才计成功"],
  notCovered: ["判定 JSON 与对象池 id 的一致性校验在主会话的 merge 脚本中做，workflow 内未做"],
};
