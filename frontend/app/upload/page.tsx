'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file) {
      setError('请选择 PDF 文件');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);

    try {
      const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${baseURL}/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        throw new Error('上传失败');
      }
      const data = await res.json();
      router.push(`/paper/${data.paper_id}`);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="max-w-md mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">上传学术论文 PDF</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="file-input file-input-bordered w-full"
        />
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <button
          type="submit"
          className="btn btn-primary w-full"
          disabled={!file}
        >
          开始解析
        </button>
      </form>
    </div>
  );
} 