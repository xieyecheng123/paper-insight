'use client';

import { useParams } from 'next/navigation';
import useSWR from 'swr';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusTracker } from '@/components/ui/StatusTracker';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface Analysis {
  title: string;
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
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  analysis: Analysis | null;
}

function ResultSkeleton() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4">
      <StatusTracker />
    </main>
  );
}

const analysisSections = [
  { key: 'exec_summary', title: '执行摘要' },
  { key: 'background', title: '研究背景与动机' },
  { key: 'methods', title: '核心概念与方法' },
  { key: 'results', title: '实验与结果分析' },
  { key: 'discussion', title: '讨论与评价' },
  { key: 'quick_ref', title: '关键信息快速参考' },
];

export default function PaperPage() {
  const params = useParams();
  const { id } = params;

  const { data: paper, error } = useSWR<Paper>(
    id ? `/api/paper/${id}` : null,
    fetcher,
    {
      refreshInterval: (latestData) => {
        if (latestData?.status === 'COMPLETED' || latestData?.status === 'FAILED') {
          return 0;
        }
        return 3000;
      },
    }
  );

  if (error) return <div className="p-8 text-center text-red-500">加载数据失败，请刷新页面。</div>;
  if (!paper || paper.status === 'PROCESSING' || paper.status === 'PENDING') {
    return <ResultSkeleton />;
  }

  if (paper.status === 'FAILED') {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-8">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-xl font-semibold text-red-600">解析失败</CardTitle>
          </CardHeader>
          <CardContent>
            <p>服务器在解析过程中出现错误，请返回上传页面重试。</p>
          </CardContent>
        </Card>
      </main>
    );
  }

  const { analysis } = paper;
  if (!analysis) {
    return <div className="p-8 text-center">分析数据为空，可能仍在处理中。</div>;
  }

  return (
    <main className="flex min-h-screen flex-col items-center p-4 sm:p-8">
      <div className="w-full max-w-3xl">
        <h1 className="text-2xl sm:text-3xl font-bold mb-2 text-center">论文解析结果</h1>
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-center text-muted-foreground">
          {analysis.title}
        </h2>
        <p className="text-sm text-muted-foreground mb-6 text-center truncate">
          文件名: {paper.filename}
        </p>
        <Accordion type="single" collapsible defaultValue="exec_summary" className="w-full">
          {analysisSections.map((section) => (
            <AccordionItem key={section.key} value={section.key}>
              <AccordionTrigger className="text-lg font-semibold">{section.title}</AccordionTrigger>
              <AccordionContent className="text-base leading-relaxed">
                {analysis[section.key as keyof Analysis]}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </main>
  );
} 