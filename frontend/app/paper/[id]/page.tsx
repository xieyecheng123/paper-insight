'use client';

import { useParams } from 'next/navigation';
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface Analysis {
  exec_summary: string;
  background: string;
  methods: string;
  results: string;
  discussion: string;
  quick_ref: string;
}

interface Paper {
  paper_id: number;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  analysis: Analysis | null;
}

export default function PaperPage() {
  const params = useParams();
  const { id } = params;

  const { data: paper, error } = useSWR<Paper>(
    id ? `/api/paper/${id}` : null,
    fetcher,
    {
      refreshInterval: (latestData) => {
        if (latestData?.status === 'completed' || latestData?.status === 'error') {
          return 0;
        }
        return 3000;
      },
    }
  );

  if (error) return <div className="p-8">加载数据失败，请刷新页面。</div>;
  if (!paper) return <div className="p-8">正在加载...</div>;

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
        <p className="text-sm text-gray-500 mt-2">页面正在自动刷新，请稍候...</p>
      </div>
    );
  }

  const { analysis } = paper;
  if (!analysis) {
    return <div className="p-8">解析数据为空。</div>;
  }

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