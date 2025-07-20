'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import useSWR from 'swr';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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

// 1. 将分析部分的定义移到外部，方便复用
const analysisSections = [
  { key: 'exec_summary', title: '执行摘要' },
  { key: 'background', title: '研究背景与动机' },
  { key: 'methods', title: '核心概念与方法' },
  { key: 'results', title: '实验与结果分析' },
  { key: 'discussion', title: '讨论与评价' },
  { key: 'quick_ref', title: '关键信息快速参考' },
];

function ResultSkeleton() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4">
      <StatusTracker />
    </main>
  );
}

// 2. 创建一个专门用于展示结果的子组件
function PaperResultDisplay({ paper }: { paper: Paper }) {
  const { analysis } = paper;

  // 1. 状态从一个空数组开始。
  const [openSections, setOpenSections] = useState<string[]>([]);

  // 2. effect 钩子会在组件首次挂载后运行一次。
  //    由于父组件的 key 属性保证了这是一个全新的组件，
  //    这个 effect 能确保在最可靠的时机设置展开状态。
  useEffect(() => {
    setOpenSections(analysisSections.map((s) => s.key));
  }, []); // 空依赖数组 [] 保证了它只运行一次。

  if (!analysis) {
    return <div className="p-8 text-center">分析数据为空。</div>;
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
        <Accordion
          type="multiple"
          value={openSections}
          onValueChange={setOpenSections}
          className="w-full"
        >
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
  
  // 仅在加载中时显示骨架屏
  if (!paper || paper.status === 'PROCESSING' || paper.status === 'PENDING') {
    return <ResultSkeleton />;
  }

  // 在失败时显示错误信息
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
  
  // 4. 为 PaperResultDisplay 添加 key 属性，强制其在 paper 数据加载完成后重新挂载。
  // 这能确保其内部 state 被干净地初始化。
  return <PaperResultDisplay key={paper.paper_id} paper={paper} />;
} 