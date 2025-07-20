'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, Loader } from 'lucide-react';

const steps = [
  '文件上传成功，任务已创建',
  '正在提取论文文本内容...',
  '正在发送至 AI 模型进行分析...',
  '正在接收和处理分析结果...',
  '正在保存至数据库...',
  '即将完成...',
];

export function StatusTracker() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const timers = steps.map((_, index) =>
      setTimeout(() => {
        setCurrentStep(index + 1);
      }, (index + 1) * 1500) // 每 1.5 秒更新一步
    );

    // 组件卸载时清除所有定时器，防止内存泄漏
    return () => {
      timers.forEach(clearTimeout);
    };
  }, []);

  return (
    <div className="w-full max-w-2xl mx-auto p-4 sm:p-8">
      <div className="bg-card p-6 rounded-lg shadow-md border">
        <h2 className="text-xl sm:text-2xl font-semibold mb-6 text-center">
          正在深度解析您的论文...
        </h2>
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div
              key={index}
              className={`flex items-center transition-opacity duration-500 ${
                index < currentStep ? 'opacity-100' : 'opacity-40'
              }`}
            >
              {index < currentStep - 1 ? (
                <CheckCircle className="w-5 h-5 mr-3 text-green-500 flex-shrink-0" />
              ) : index === currentStep - 1 ? (
                <Loader className="w-5 h-5 mr-3 animate-spin text-primary flex-shrink-0" />
              ) : (
                <div className="w-5 h-5 mr-3 border-2 border-muted rounded-full flex-shrink-0" />
              )}
              <span className="text-base text-foreground">{step}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 