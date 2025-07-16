import 'server-only';
import PaperStatusTracker from './paper-status-tracker';

interface Props {
  params: {
    id: string;
  };
}

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
  const initialPaperData = await fetchPaper(params.id);

  if (!initialPaperData) {
    return <div className="p-8">未找到该论文或加载失败。</div>;
  }

  return <PaperStatusTracker initialData={initialPaperData} paperId={params.id} />;
} 