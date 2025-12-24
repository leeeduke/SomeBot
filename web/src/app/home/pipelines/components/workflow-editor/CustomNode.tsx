'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Card } from '@/components/ui/card';
import {
  Play,
  Clock,
  GitBranch,
  Globe,
  Database,
  FileJson,
  MessageSquare,
  Variable,
  Settings,
  GitMerge,
  Pickaxe,
  StopCircle,
} from 'lucide-react';

const nodeIcons: { [key: string]: any } = {
  event_start: Play,
  schedule_start: Clock,
  condition: GitBranch,
  chat_command_branch: GitMerge,
  http_request: Globe,
  binary_storage: Database,
  file_storage: Database,
  json_processor: FileJson,
  reply_message: MessageSquare,
  tool_action: Pickaxe,
  set_variable: Variable,
  get_variable: Variable,
  end: StopCircle,
};

const nodeColors: { [key: string]: string } = {
  event_start: 'bg-green-100 border-green-300 dark:bg-green-900/50 dark:border-green-700',
  schedule_start: 'bg-blue-100 border-blue-300 dark:bg-blue-900/50 dark:border-blue-700',
  condition: 'bg-yellow-100 border-yellow-300 dark:bg-yellow-900/50 dark:border-yellow-700',
  chat_command_branch: 'bg-orange-100 border-orange-300 dark:bg-orange-900/50 dark:border-orange-700',
  http_request: 'bg-purple-100 border-purple-300 dark:bg-purple-900/50 dark:border-purple-700',
  binary_storage: 'bg-gray-100 border-gray-300 dark:bg-gray-800/50 dark:border-gray-600',
  file_storage: 'bg-gray-100 border-gray-300 dark:bg-gray-800/50 dark:border-gray-600',
  json_processor: 'bg-indigo-100 border-indigo-300 dark:bg-indigo-900/50 dark:border-indigo-700',
  reply_message: 'bg-pink-100 border-pink-300 dark:bg-pink-900/50 dark:border-pink-700',
  tool_action: 'bg-teal-100 border-teal-300 dark:bg-teal-900/50 dark:border-teal-700',
  set_variable: 'bg-cyan-100 border-cyan-300 dark:bg-cyan-900/50 dark:border-cyan-700',
  get_variable: 'bg-cyan-100 border-cyan-300 dark:bg-cyan-900/50 dark:border-cyan-700',
  end: 'bg-red-100 border-red-300 dark:bg-red-900/50 dark:border-red-700',
};

function CustomNode({ data, selected }: NodeProps) {
  const nodeData = data as any;
  const Icon = nodeIcons[nodeData.type] || Settings;
  const colorClass = nodeColors[nodeData.type] || 'bg-gray-100 border-gray-300 dark:bg-gray-800/50 dark:border-gray-600';

  const isStartNode = nodeData.type === 'event_start' || nodeData.type === 'schedule_start';
  const isEndNode = nodeData.type === 'end';

  return (
    <>
      {!isStartNode && (
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 !bg-primary"
        />
      )}
      <Card
        className={`px-4 py-2 shadow-md ${colorClass} ${
          selected ? 'ring-2 ring-primary' : ''
        } min-w-[180px]`}
      >
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5" />
          <div className="flex-1">
            <div className="text-sm font-medium">{nodeData.label}</div>
            {nodeData.description && (
              <div className="text-xs text-muted-foreground mt-1">
                {nodeData.description}
              </div>
            )}
          </div>
        </div>
      </Card>
      {!isEndNode && (
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 !bg-primary"
        />
      )}
    </>
  );
}

export default memo(CustomNode);