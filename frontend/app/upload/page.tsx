'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Loader2, FileUp } from 'lucide-react';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type !== 'application/pdf') {
        setError('文件格式不正确，请上传 PDF 文件。');
        setFile(null);
      } else {
        setError(null);
        setFile(selectedFile);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file) {
      setError('请选择一个 PDF 文件。');
      return;
    }
    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`/api/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || '上传失败，请稍后重试。');
      }
      
      router.push(`/paper/${data.id}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '发生未知错误。';
      setError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-50 dark:bg-gray-900">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">论文智能解析</CardTitle>
          <CardDescription>
            上传您的 PDF 格式学术论文，我们将为您深度解析。
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-center w-full">
              <label
                htmlFor="dropzone-file"
                className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 dark:border-gray-600 dark:hover:border-gray-500 dark:bg-gray-700 dark:hover:bg-gray-600"
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <FileUp className="w-10 h-10 mb-3 text-gray-400" />
                  <p className="mb-2 text-sm text-center text-gray-500 dark:text-gray-400">
                    {file ? (
                      <span className="font-semibold text-green-600">{file.name}</span>
                    ) : (
                      <>
                        <span className="font-semibold">点击选择文件</span> 或拖拽到此处
                      </>
                    )}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">仅支持 PDF 格式</p>
                </div>
                <Input
                  id="dropzone-file"
                  type="file"
                  className="hidden"
                  accept="application/pdf"
                  onChange={handleFileChange}
                  disabled={isUploading}
                />
              </label>
            </div>
            {error && <p className="text-sm font-medium text-red-500">{error}</p>}
          </CardContent>
          <CardFooter>
            <Button
              type="submit"
              className="w-full"
              disabled={!file || isUploading}
            >
              {isUploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  正在解析...
                </>
              ) : (
                '开始解析'
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </main>
  );
} 