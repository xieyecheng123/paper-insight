import 'server-only';

interface Props {
  params: {
    id: string;
  };
}

export const dynamic = 'force-dynamic';

async function fetchPaper(id: string) {
  const res = await fetch(`http://backend:8000/paper/${id}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    return null;
  }
  return res.json();
}

export default async function PaperPage({ params }: Props) {
  const paper = await fetchPaper(params.id);
  if (!paper) {
    return <div className="p-8">未找到该论文。</div>;
  }

  if (paper.status === 'error') {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <h1 className="text-xl font-semibold mb-2">解析失败</h1>
        <p className="text-red-500">服务器在解析过程中出现错误，请稍后重试。</p>
      </div>
    );
  }

  if (paper.status !== 'completed') {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <h1 className="text-xl font-semibold mb-2">解析进度</h1>
        <p>当前状态：{paper.status}</p>
        <p className="text-sm text-gray-500 mt-2">请稍后刷新页面。</p>
      </div>
    );
  }

  const { analysis } = paper;
  return (
    <div className="max-w-3xl mx-auto p-8 space-y-6">
      <h1 className="text-2xl font-bold mb-4">解析结果</h1>

      <section>
        <h2 className="font-semibold mb-1">执行摘要</h2>
        <p>{analysis.exec_summary}</p>
      </section>

      <section>
        <h2 className="font-semibold mb-1">研究背景与动机</h2>
        <p>{analysis.background}</p>
      </section>

      <section>
        <h2 className="font-semibold mb-1">核心概念与方法</h2>
        <p>{analysis.methods}</p>
      </section>

      <section>
        <h2 className="font-semibold mb-1">实验与结果分析</h2>
        <p>{analysis.results}</p>
      </section>

      <section>
        <h2 className="font-semibold mb-1">讨论与评价</h2>
        <p>{analysis.discussion}</p>
      </section>

      <section>
        <h2 className="font-semibold mb-1">快速参考</h2>
        <p>{analysis.quick_ref}</p>
      </section>
    </div>
  );
} 