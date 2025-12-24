'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
  Loader2,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { httpClient } from '@/app/infra/http/HttpClient';
import { extractI18nObject } from '@/i18n/I18nProvider';

interface NodePaletteProps {
  onAddNode: (nodeType: string) => void;
}

// Icon mapping for node types
const nodeIcons: Record<string, any> = {
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

export default function NodePalette({ onAddNode }: NodePaletteProps) {
  const { t } = useTranslation();
  const [nodeCategories, setNodeCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNodeManifests();
  }, []);

  const loadNodeManifests = async () => {
    try {
      setLoading(true);
      const data = await httpClient.getWorkflowNodes();

      // Group nodes by category
      const grouped: Record<string, any[]> = {};

      data.nodes.forEach((node: any) => {
        const category = node.spec?.category || 'general';
        if (!grouped[category]) {
          grouped[category] = [];
        }

        // Use extractI18nObject to get localized text
        const label = node.label ? extractI18nObject(node.label) : node.name;
        const description = node.description ? extractI18nObject(node.description) : '';

        grouped[category].push({
          type: node.name,
          label,
          description,
          icon: nodeIcons[node.name] || Settings,
          color: node.spec?.color || '#666',
        });
      });

      // Convert to categories array with localized category names
      const categoryNames: Record<string, any> = {
        start: t('workflow.categories.start'),
        control: t('workflow.categories.control'),
        action: t('workflow.categories.action'),
        general: t('workflow.categories.general'),
      };

      const categories = Object.entries(grouped).map(([category, nodes]) => ({
        name: categoryNames[category] || category,
        nodes,
      }));

      setNodeCategories(categories);
    } catch (error) {
      console.error('Failed to load node manifests:', error);
      // Fallback to default nodes if API fails
      setNodeCategories([
        {
          name: t('workflow.categories.start'),
          nodes: [
            {
              type: 'event_start',
              label: t('workflow.nodes.eventStart'),
              icon: Play,
              description: t('workflow.nodes.eventStartDesc'),
            },
          ],
        },
        {
          name: t('workflow.categories.action'),
          nodes: [
            {
              type: 'reply_message',
              label: t('workflow.nodes.replyMessage'),
              icon: MessageSquare,
              description: t('workflow.nodes.replyMessageDesc'),
            },
          ],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground mt-2">{t('common.loading')}</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden max-w-full">
      <h3 className="font-semibold mb-4 px-1 truncate">{t('workflow.nodePalette')}</h3>
      <div className="flex-1 overflow-y-auto overflow-x-hidden pr-2">
        <div className="space-y-4 max-w-full">
          {nodeCategories.map((category) => (
            <div key={category.name} className="w-full">
              <h4 className="text-sm font-medium text-muted-foreground mb-2 truncate">
                {category.name}
              </h4>
              <div className="space-y-2 w-full">
                {category.nodes.map((node: any) => {
                  const Icon = node.icon;
                  return (
                    <Card
                      key={node.type}
                      className="p-2 cursor-move hover:bg-accent transition-colors overflow-hidden"
                      draggable
                      onDragStart={(e) => handleDragStart(e, node.type)}
                      onClick={() => onAddNode(node.type)}
                      style={{ width: '100%', maxWidth: '100%', boxSizing: 'border-box' }}
                    >
                      <div className="flex items-center gap-2 overflow-hidden" style={{ width: '100%', maxWidth: '100%' }}>
                        <Icon
                          className="w-4 h-4 flex-shrink-0"
                          style={{ color: node.color || '#6B7280' }}
                        />
                        <div className="flex-1 overflow-hidden" style={{ minWidth: 0, maxWidth: '100%' }}>
                          <p className="text-sm font-medium truncate" style={{ wordBreak: 'break-all', overflowWrap: 'break-word' }}>
                            {node.label}
                          </p>
                          <p className="text-xs text-muted-foreground truncate" style={{ wordBreak: 'break-all', overflowWrap: 'break-word' }}>
                            {node.description}
                          </p>
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}