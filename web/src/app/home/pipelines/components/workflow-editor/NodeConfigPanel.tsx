'use client';

import React, { useState, useEffect } from 'react';
import { Node } from '@xyflow/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { X, Trash2, Save } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface NodeConfigPanelProps {
  node: Node;
  onUpdate: (updates: any) => void;
  onDelete: () => void;
  onClose: () => void;
}

export default function NodeConfigPanel({ node, onUpdate, onDelete, onClose }: NodeConfigPanelProps) {
  const [nodeData, setNodeData] = useState<any>(node.data);
  const [config, setConfig] = useState<any>((node.data as any).config || {});

  useEffect(() => {
    setNodeData(node.data);
    setConfig((node.data as any).config || {});
  }, [node]);

  const handleUpdate = () => {
    onUpdate({
      ...nodeData,
      config,
    });
  };

  const renderConfigFields = () => {
    switch (nodeData.type) {
      case 'event_start':
        return (
          <div className="space-y-4">
            <div>
              <Label>Trigger Type</Label>
              <Select
                value={config.trigger_type || 'person_message'}
                onValueChange={(value) => setConfig({ ...config, trigger_type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="person_message">Person Message</SelectItem>
                  <SelectItem value="group_message">Group Message</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Filters (JSON)</Label>
              <Textarea
                value={JSON.stringify(config.filters || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const filters = JSON.parse(e.target.value);
                    setConfig({ ...config, filters });
                  } catch (err) {
                    // Invalid JSON, ignore
                  }
                }}
                placeholder='{"user_id": "123"}'
                className="font-mono"
              />
            </div>
          </div>
        );

      case 'schedule_start':
        return (
          <div className="space-y-4">
            <div>
              <Label>Cron Expression</Label>
              <Input
                value={config.cron_expression || ''}
                onChange={(e) => setConfig({ ...config, cron_expression: e.target.value })}
                placeholder="0 0 * * *"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Format: minute hour day month weekday
              </p>
            </div>
            <div>
              <Label>Timezone</Label>
              <Input
                value={config.timezone || 'UTC'}
                onChange={(e) => setConfig({ ...config, timezone: e.target.value })}
                placeholder="UTC"
              />
            </div>
          </div>
        );

      case 'http_request':
        return (
          <div className="space-y-4">
            <div>
              <Label>Method</Label>
              <Select
                value={config.method || 'GET'}
                onValueChange={(value) => setConfig({ ...config, method: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GET">GET</SelectItem>
                  <SelectItem value="POST">POST</SelectItem>
                  <SelectItem value="PUT">PUT</SelectItem>
                  <SelectItem value="DELETE">DELETE</SelectItem>
                  <SelectItem value="PATCH">PATCH</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>URL</Label>
              <Input
                value={config.url || ''}
                onChange={(e) => setConfig({ ...config, url: e.target.value })}
                placeholder="https://api.example.com/endpoint"
              />
            </div>
            <div>
              <Label>Headers (JSON)</Label>
              <Textarea
                value={JSON.stringify(config.headers || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const headers = JSON.parse(e.target.value);
                    setConfig({ ...config, headers });
                  } catch (err) {
                    // Invalid JSON, ignore
                  }
                }}
                placeholder='{"Content-Type": "application/json"}'
                className="font-mono"
              />
            </div>
            <div>
              <Label>Body (JSON)</Label>
              <Textarea
                value={JSON.stringify(config.body || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const body = JSON.parse(e.target.value);
                    setConfig({ ...config, body });
                  } catch (err) {
                    // Invalid JSON, ignore
                  }
                }}
                className="font-mono"
              />
            </div>
          </div>
        );

      case 'json_processor':
        return (
          <div className="space-y-4">
            <div>
              <Label>Operation</Label>
              <Select
                value={config.operation || 'extract'}
                onValueChange={(value) => setConfig({ ...config, operation: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="extract">Extract Value</SelectItem>
                  <SelectItem value="set">Set Value</SelectItem>
                  <SelectItem value="serialize">Serialize to JSON</SelectItem>
                  <SelectItem value="deserialize">Deserialize from JSON</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {(config.operation === 'extract' || config.operation === 'set') && (
              <div>
                <Label>Path</Label>
                <Input
                  value={config.path || ''}
                  onChange={(e) => setConfig({ ...config, path: e.target.value })}
                  placeholder="data.items.0.name"
                />
              </div>
            )}
            {config.operation === 'set' && (
              <div>
                <Label>Value</Label>
                <Textarea
                  value={JSON.stringify(config.value || '', null, 2)}
                  onChange={(e) => {
                    try {
                      const value = JSON.parse(e.target.value);
                      setConfig({ ...config, value });
                    } catch (err) {
                      setConfig({ ...config, value: e.target.value });
                    }
                  }}
                  className="font-mono"
                />
              </div>
            )}
          </div>
        );

      case 'reply_message':
        return (
          <div className="space-y-4">
            <div>
              <Label>Message Content</Label>
              <Textarea
                value={config.content || ''}
                onChange={(e) => setConfig({ ...config, content: e.target.value })}
                placeholder="Hello! This is a reply message."
              />
              <p className="text-xs text-muted-foreground mt-1">
                Use ${`{variable_name}`} to insert variables
              </p>
            </div>
            <div>
              <Label>Reply To (Message ID)</Label>
              <Input
                value={config.reply_to || ''}
                onChange={(e) => setConfig({ ...config, reply_to: e.target.value })}
                placeholder="Optional: specific message ID to reply to"
              />
            </div>
          </div>
        );

      case 'set_variable':
      case 'get_variable':
        return (
          <div className="space-y-4">
            <div>
              <Label>Variable Name</Label>
              <Input
                value={config.variable_name || ''}
                onChange={(e) => setConfig({ ...config, variable_name: e.target.value })}
                placeholder="my_variable"
              />
            </div>
            {nodeData.type === 'set_variable' && (
              <div>
                <Label>Value</Label>
                <Textarea
                  value={JSON.stringify(config.value || '', null, 2)}
                  onChange={(e) => {
                    try {
                      const value = JSON.parse(e.target.value);
                      setConfig({ ...config, value });
                    } catch (err) {
                      setConfig({ ...config, value: e.target.value });
                    }
                  }}
                  placeholder="Variable value (can be JSON)"
                  className="font-mono"
                />
              </div>
            )}
            {nodeData.type === 'get_variable' && (
              <div>
                <Label>Default Value</Label>
                <Input
                  value={config.default || ''}
                  onChange={(e) => setConfig({ ...config, default: e.target.value })}
                  placeholder="Default value if variable doesn't exist"
                />
              </div>
            )}
          </div>
        );

      case 'condition':
        return (
          <div className="space-y-4">
            <div>
              <Label>Conditions (JSON Array)</Label>
              <Textarea
                value={JSON.stringify(config.conditions || [], null, 2)}
                onChange={(e) => {
                  try {
                    const conditions = JSON.parse(e.target.value);
                    setConfig({ ...config, conditions });
                  } catch (err) {
                    // Invalid JSON, ignore
                  }
                }}
                placeholder='[{"type": "equals", "field": "status", "value": "active"}]'
                className="font-mono h-32"
              />
            </div>
            <div>
              <Label>Default Branch</Label>
              <Input
                value={config.default_branch || 'default'}
                onChange={(e) => setConfig({ ...config, default_branch: e.target.value })}
                placeholder="default"
              />
            </div>
          </div>
        );

      case 'tool_action':
        return (
          <div className="space-y-4">
            <div>
              <Label>Tool ID</Label>
              <Input
                value={config.tool_id || ''}
                onChange={(e) => setConfig({ ...config, tool_id: e.target.value })}
                placeholder="plugin.tool_name"
              />
            </div>
            <div>
              <Label>Parameters (JSON)</Label>
              <Textarea
                value={JSON.stringify(config.parameters || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const parameters = JSON.parse(e.target.value);
                    setConfig({ ...config, parameters });
                  } catch (err) {
                    // Invalid JSON, ignore
                  }
                }}
                placeholder='{"param1": "value1"}'
                className="font-mono"
              />
            </div>
          </div>
        );

      default:
        return (
          <div className="text-muted-foreground">
            No configuration options for this node type.
          </div>
        );
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="font-semibold">Node Configuration</h3>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4">
          <Tabs defaultValue="general">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="general">General</TabsTrigger>
              <TabsTrigger value="config">Configuration</TabsTrigger>
            </TabsList>

            <TabsContent value="general" className="space-y-4">
              <div>
                <Label>Node ID</Label>
                <Input value={node.id} disabled />
              </div>
              <div>
                <Label>Node Type</Label>
                <Badge variant="outline">{nodeData.type}</Badge>
              </div>
              <div>
                <Label>Label</Label>
                <Input
                  value={nodeData.label}
                  onChange={(e) => setNodeData({ ...nodeData, label: e.target.value })}
                />
              </div>
              <div>
                <Label>Description</Label>
                <Textarea
                  value={nodeData.description || ''}
                  onChange={(e) => setNodeData({ ...nodeData, description: e.target.value })}
                  placeholder="Optional description"
                />
              </div>
              <Separator />
              <div>
                <Label>Advanced Settings</Label>
                <div className="space-y-2 mt-2">
                  <div>
                    <Label className="text-sm">Timeout (seconds)</Label>
                    <Input
                      type="number"
                      value={config.timeout || ''}
                      onChange={(e) => setConfig({ ...config, timeout: parseInt(e.target.value) || undefined })}
                      placeholder="No timeout"
                    />
                  </div>
                  <div>
                    <Label className="text-sm">Retry Count</Label>
                    <Input
                      type="number"
                      value={config.retry || ''}
                      onChange={(e) => setConfig({ ...config, retry: parseInt(e.target.value) || undefined })}
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <Label className="text-sm">Error Handler</Label>
                    <Select
                      value={config.error_handler || 'fail'}
                      onValueChange={(value) => setConfig({ ...config, error_handler: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="fail">Fail Workflow</SelectItem>
                        <SelectItem value="skip">Skip Node</SelectItem>
                        <SelectItem value="retry">Retry Node</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="config" className="space-y-4">
              {renderConfigFields()}
            </TabsContent>
          </Tabs>
        </div>
      </ScrollArea>

      <div className="flex gap-2 p-4 border-t">
        <Button
          variant="destructive"
          onClick={onDelete}
          className="flex items-center gap-2"
        >
          <Trash2 className="h-4 w-4" />
          Delete
        </Button>
        <Button
          onClick={handleUpdate}
          className="flex-1 flex items-center justify-center gap-2"
        >
          <Save className="h-4 w-4" />
          Apply Changes
        </Button>
      </div>
    </div>
  );
}