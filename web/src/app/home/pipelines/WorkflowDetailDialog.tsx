'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Node,
  BackgroundVariant,
  NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Save, Play, Trash2, Download, Bug, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { httpClient } from '@/app/infra/http/HttpClient';
import { extractI18nObject } from '@/i18n/I18nProvider';
import NodePalette from './components/workflow-editor/NodePalette';
import NodeConfigPanel from './components/workflow-editor/NodeConfigPanel';
import CustomNode from './components/workflow-editor/CustomNode';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from '@/components/ui/sidebar';

interface WorkflowDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workflowId?: string;
  isEditMode: boolean;
  onFinish: () => void;
  onNewWorkflowCreated: (workflowId: string) => void;
  onDeleteWorkflow: () => void;
  onCancel: () => void;
}

interface NodeManifest {
  name: string;
  label?: any;
  description?: any;
  spec?: {
    category?: string;
    color?: string;
  };
}

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

type DialogMode = 'editor' | 'settings' | 'debug';

export default function WorkflowDetailDialog({
  open,
  onOpenChange,
  workflowId,
  isEditMode,
  onFinish,
  onNewWorkflowCreated,
  onDeleteWorkflow,
  onCancel,
}: WorkflowDetailDialogProps) {
  const { t } = useTranslation();
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const [selectedNode, setSelectedNode] = useState<Node<any> | null>(null);
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [currentMode, setCurrentMode] = useState<DialogMode>('editor');
  const [nodeManifests, setNodeManifests] = useState<Record<string, NodeManifest>>({});

  useEffect(() => {
    // Load node manifests when dialog opens
    if (open) {
      loadNodeManifests();
    }

    if (open && workflowId && isEditMode) {
      loadWorkflow();
    } else if (open && !isEditMode) {
      // Clear for new workflow
      setWorkflowName('');
      setWorkflowDescription('');
      setNodes([]);
      setEdges([]);
      setSelectedNode(null);
      setCurrentMode('editor');
    }
  }, [open, workflowId, isEditMode]);

  const loadNodeManifests = async () => {
    try {
      const data = await httpClient.getWorkflowNodes();
      const manifestMap: Record<string, NodeManifest> = {};

      data.nodes.forEach((node: NodeManifest) => {
        manifestMap[node.name] = node;
      });

      setNodeManifests(manifestMap);
    } catch (error) {
      console.error('Failed to load node manifests:', error);
    }
  };

  const loadWorkflow = async () => {
    try {
      const data = await httpClient.getWorkflow(workflowId!);
      const workflowData = data.workflow;

      setWorkflowName(workflowData.name);
      setWorkflowDescription(workflowData.description || '');

      // Convert workflow nodes to react-flow nodes
      const flowNodes = (workflowData.nodes || []).map((node: any) => {
        // Try to get localized label from manifest
        const manifest = nodeManifests[node.type];
        let label = node.name;
        if (manifest && manifest.label) {
          label = extractI18nObject(manifest.label);
        }

        return {
          id: node.id,
          type: 'custom',
          position: node.position || {
            x: 100 + Math.random() * 400,
            y: 100 + Math.random() * 400,
          },
          data: {
            label: label,
            type: node.type,
            config: node.config,
            description: node.description,
          },
        };
      });

      // Convert workflow edges to react-flow edges
      const flowEdges = (workflowData.edges || []).map((edge: any) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: null,
        targetHandle: null,
        label: edge.label,
        data: edge.condition,
        type: 'smoothstep',
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (error) {
      console.error('Error loading workflow:', error);
      toast.error(t('workflow.loadFailed'));
    }
  };

  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        id: `edge-${Date.now()}`,
        type: 'smoothstep',
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges],
  );

  const onNodeClick = useCallback((_: any, node: Node<any>) => {
    setSelectedNode(node);
  }, []);

  const handleAddNode = (nodeType: string) => {
    // Get the manifest for this node type
    const manifest = nodeManifests[nodeType];

    // Use localized label from manifest, fallback to hardcoded label
    let label = `New ${nodeType} Node`;
    if (manifest && manifest.label) {
      label = extractI18nObject(manifest.label);
    }

    const newNode: Node<any> = {
      id: `node-${Date.now()}`,
      type: 'custom',
      position: {
        x: Math.random() * 400 + 100,
        y: Math.random() * 400 + 100,
      },
      data: {
        label: label,
        type: nodeType,
        config: {},
      },
    };
    setNodes((nds) => nds.concat(newNode));
  };

  const handleUpdateNode = (nodeId: string, updates: any) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...updates } }
          : node,
      ),
    );
  };

  const handleDeleteNode = (nodeId: string) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) =>
      eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId),
    );
    setSelectedNode(null);
  };

  const handleCreateWorkflow = async () => {
    if (!workflowName) {
      toast.error(t('workflow.nameRequired'));
      return;
    }

    setIsSaving(true);
    try {
      const workflow = {
        name: workflowName,
        description: workflowDescription,
        nodes: [],
        edges: [],
        trigger_types: ['person_message'],
        status: 'active',
      };

      const data = await httpClient.createWorkflow(workflow);
      const newWorkflowId = data.workflow.id;

      toast.success(t('workflow.createSuccess'));
      onNewWorkflowCreated(newWorkflowId);
    } catch (error) {
      console.error('Error creating workflow:', error);
      toast.error(t('workflow.createError'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveWorkflow = async () => {
    if (!workflowName) {
      toast.error(t('workflow.nameRequired'));
      return;
    }

    if (!workflowId) return;

    setIsSaving(true);
    try {
      // Convert react-flow nodes back to workflow nodes
      const workflowNodes = nodes.map((node) => ({
        id: node.id,
        type: node.data.type,
        name: node.data.label,
        description: node.data.description,
        position: node.position,
        config: node.data.config || {},
      }));

      // Convert react-flow edges back to workflow edges
      const workflowEdges = edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        condition: edge.data,
      }));

      const workflow = {
        name: workflowName,
        description: workflowDescription,
        nodes: workflowNodes,
        edges: workflowEdges,
        trigger_types: ['person_message'],
        status: 'active',
      };

      await httpClient.updateWorkflow(workflowId, workflow);

      toast.success(t('workflow.saveSuccess'));
      onFinish();
    } catch (error) {
      console.error('Error saving workflow:', error);
      toast.error(t('workflow.saveError'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (
      !workflowId ||
      !confirm(t('workflow.deleteConfirmation'))
    )
      return;

    try {
      await httpClient.deleteWorkflow(workflowId);
      toast.success(t('workflow.deleteSuccess'));
      onDeleteWorkflow();
    } catch (error) {
      console.error('Error deleting workflow:', error);
      toast.error(t('workflow.deleteError'));
    }
  };

  const handleExecute = async () => {
    if (!workflowId) return;

    try {
      const data = await httpClient.executeWorkflow(workflowId, {
        trigger_data: {},
      });
      toast.success(
        t('workflow.executeSuccess', { id: data.execution_id }),
      );
    } catch (error) {
      console.error('Error executing workflow:', error);
      toast.error(t('workflow.executeFailed'));
    }
  };

  const handleExport = async () => {
    if (!workflowId) return;

    try {
      const blob = await httpClient.exportWorkflow(workflowId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `workflow_${workflowId}.yaml`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);

      toast.success(t('workflow.exportSuccess'));
    } catch (error) {
      console.error('Error exporting workflow:', error);
      toast.error(t('workflow.exportFailed'));
    }
  };

  const menu = [
    {
      key: 'editor',
      label: t('workflow.visualEditor'),
      icon: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-4 h-4"
        >
          <path d="M13.196 2.268a3.245 3.245 0 0 0-2.392 0l-7.5 3A3.25 3.25 0 0 0 1.5 8.355v7.29a3.25 3.25 0 0 0 1.804 3.087l7.5 3a3.245 3.245 0 0 0 2.392 0l7.5-3a3.25 3.25 0 0 0 1.804-3.087v-7.29a3.25 3.25 0 0 0-1.804-3.087l-7.5-3Z" />
        </svg>
      ),
    },
    {
      key: 'settings',
      label: t('workflow.settings'),
      icon: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-4 h-4"
        >
          <path fillRule="evenodd" d="M11.078 2.25c-.917 0-1.699.663-1.855 1.567L8.982 5.08c-.092.499-.556.913-1.11.913h-.312c-.809 0-1.557-.421-1.973-1.11l-.6-.992a1.875 1.875 0 0 0-2.817-.062 1.875 1.875 0 0 0-.062 2.817l.992.6c.689.416 1.11 1.164 1.11 1.973v.312c0 .554-.414 1.018-.913 1.11l-1.262.241a1.875 1.875 0 0 0-1.567 1.855c0 .917.663 1.699 1.567 1.855l1.262.241c.499.092.913.556.913 1.11v.312c0 .809-.421 1.557-1.11 1.973l-.992.6a1.875 1.875 0 0 0 .062 2.817 1.875 1.875 0 0 0 2.817.062l.6-.992c.416-.689 1.164-1.11 1.973-1.11h.312c.554 0 1.018.414 1.11.913l.241 1.262a1.875 1.875 0 0 0 1.855 1.567c.917 0 1.699-.663 1.855-1.567l.241-1.262c.092-.499.556-.913 1.11-.913h.312c.809 0 1.557.421 1.973 1.11l.6.992a1.875 1.875 0 0 0 2.817.062 1.875 1.875 0 0 0 .062-2.817l-.992-.6a2.31 2.31 0 0 1-1.11-1.973v-.312c0-.554.414-1.018.913-1.11l1.262-.241a1.875 1.875 0 0 0 1.567-1.855c0-.917-.663-1.699-1.567-1.855l-1.262-.241a1.125 1.125 0 0 1-.913-1.11v-.312c0-.809.421-1.557 1.11-1.973l.992-.6a1.875 1.875 0 0 0-.062-2.817 1.875 1.875 0 0 0-2.817-.062l-.6.992c-.416.689-1.164 1.11-1.973 1.11h-.312a1.125 1.125 0 0 1-1.11-.913l-.241-1.262A1.875 1.875 0 0 0 12.922 2.25Zm0 8.625a2.625 2.625 0 1 1 5.25 0 2.625 2.625 0 0 1-5.25 0Z" clipRule="evenodd" />
        </svg>
      ),
    },
    {
      key: 'debug',
      label: t('workflow.debug'),
      icon: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-4 h-4"
        >
          <path fillRule="evenodd" d="M12 1.5a.75.75 0 0 1 .75.75V4.5a.75.75 0 0 1-1.5 0V2.25A.75.75 0 0 1 12 1.5ZM5.636 4.136a.75.75 0 0 1 1.06 0l1.592 1.591a.75.75 0 0 1-1.061 1.06l-1.591-1.59a.75.75 0 0 1 0-1.061Zm12.728 0a.75.75 0 0 1 0 1.06l-1.591 1.592a.75.75 0 0 1-1.06-1.061l1.59-1.591a.75.75 0 0 1 1.061 0Zm-6.816 4.496a.75.75 0 0 1 .82.311l5.228 7.917a.75.75 0 0 1-.777 1.148l-2.097-.43 1.045 3.9a.75.75 0 0 1-1.45.388l-1.044-3.899-1.601 1.42a.75.75 0 0 1-1.247-.606l.569-9.47a.75.75 0 0 1 .554-.68Z" clipRule="evenodd" />
        </svg>
      ),
    },
  ];

  const getDialogTitle = () => {
    switch (currentMode) {
      case 'editor':
        return t('workflow.visualEditor');
      case 'settings':
        return t('workflow.settings');
      case 'debug':
        return t('workflow.debug');
      default:
        return isEditMode ? t('workflow.editWorkflow') : t('workflow.createWorkflow');
    }
  };

  // Create new workflow dialog - only asks for basic info
  if (!isEditMode) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="overflow-hidden p-0 !max-w-[40vw] max-h-[70vh] flex">
          <main className="flex flex-1 flex-col h-[70vh]">
            <DialogHeader className="px-6 pt-6 pb-4 shrink-0">
              <DialogTitle>{t('workflow.createWorkflow')}</DialogTitle>
              <DialogDescription>
                {t('workflow.createDescription')}
              </DialogDescription>
            </DialogHeader>
            <div className="flex-1 overflow-y-auto px-6 pb-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="workflow-name">{t('workflow.workflowName')}</Label>
                  <Input
                    id="workflow-name"
                    value={workflowName}
                    onChange={(e) => setWorkflowName(e.target.value)}
                    placeholder={t('workflow.enterName')}
                  />
                </div>
                <div>
                  <Label htmlFor="workflow-description">{t('common.description')}</Label>
                  <Textarea
                    id="workflow-description"
                    value={workflowDescription}
                    onChange={(e) => setWorkflowDescription(e.target.value)}
                    placeholder={t('workflow.enterDescription')}
                    rows={4}
                  />
                </div>
              </div>
            </div>
            <DialogFooter className="px-6 py-4 border-t">
              <Button onClick={onCancel} variant="outline">
                {t('common.cancel')}
              </Button>
              <Button onClick={handleCreateWorkflow} disabled={isSaving}>
                {isSaving ? t('workflow.creating') : t('workflow.createWorkflow')}
              </Button>
            </DialogFooter>
          </main>
        </DialogContent>
      </Dialog>
    );
  }

  // Edit workflow dialog - full featured with sidebar
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="overflow-hidden p-0 !max-w-[80vw] h-[75vh] flex">
        <SidebarProvider className="items-start w-full flex h-full min-h-0">
          <Sidebar
            collapsible="none"
            className="hidden md:flex h-full min-h-0 w-40 border-r bg-white dark:bg-black"
          >
            <SidebarContent>
              <SidebarGroup>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {menu.map((item) => (
                      <SidebarMenuItem key={item.key}>
                        <SidebarMenuButton
                          asChild
                          isActive={currentMode === item.key}
                          onClick={() =>
                            setCurrentMode(item.key as DialogMode)
                          }
                        >
                          <a href="#">
                            <span className="mr-2">{item.icon}</span>
                            <span>{item.label}</span>
                          </a>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            </SidebarContent>
          </Sidebar>
          <main className="flex flex-1 flex-col h-full min-h-0">
            <DialogHeader
              className="px-6 pt-6 pb-4 shrink-0 flex flex-row items-center justify-between"
              style={{ height: '4rem' }}
            >
              <DialogTitle>{getDialogTitle()}</DialogTitle>
              <div className="flex items-center gap-2 pr-8">
                {isEditMode && currentMode === 'editor' && (
                  <>
                    <Button onClick={handleExecute} variant="outline" size="sm">
                      <Play className="w-4 h-4 mr-2" />
                      {t('workflow.execute')}
                    </Button>
                    <Button onClick={handleExport} variant="outline" size="sm">
                      <Download className="w-4 h-4 mr-2" />
                      {t('workflow.export')}
                    </Button>
                    <Button onClick={handleDelete} variant="destructive" size="sm">
                      <Trash2 className="w-4 h-4 mr-2" />
                      {t('common.delete')}
                    </Button>
                  </>
                )}
                <Button onClick={handleSaveWorkflow} disabled={isSaving} size="sm">
                  <Save className="w-4 h-4 mr-2" />
                  {isSaving ? t('common.saving') : t('common.save')}
                </Button>
              </div>
            </DialogHeader>
            <div
              className="flex-1 overflow-hidden w-full"
              style={{ height: 'calc(100% - 4rem)' }}
            >
              {currentMode === 'editor' && (
                <div className="flex h-full">
                  {/* Node Palette */}
                  <div className="w-64 border-r p-4 overflow-y-auto pr-2">
                    <NodePalette onAddNode={handleAddNode} />
                  </div>

                  {/* Flow Editor */}
                  <div className="flex-1 relative">
                    <ReactFlow
                      nodes={nodes}
                      edges={edges}
                      onNodesChange={onNodesChange}
                      onEdgesChange={onEdgesChange}
                      onConnect={onConnect}
                      onNodeClick={onNodeClick}
                      nodeTypes={nodeTypes}
                      fitView
                    >
                      <Background
                        variant={BackgroundVariant.Dots}
                        gap={12}
                        size={1}
                      />
                      <MiniMap />
                      <Controls />
                    </ReactFlow>
                  </div>

                  {/* Node Config Panel */}
                  {selectedNode && (
                    <div className="w-80 border-l overflow-y-auto">
                      <NodeConfigPanel
                        node={selectedNode}
                        onUpdate={(updates) =>
                          handleUpdateNode(selectedNode.id, updates)
                        }
                        onDelete={() => handleDeleteNode(selectedNode.id)}
                        onClose={() => setSelectedNode(null)}
                      />
                    </div>
                  )}
                </div>
              )}

              {currentMode === 'settings' && (
                <div className="p-6 overflow-y-auto h-full">
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="workflow-name">{t('workflow.workflowName')}</Label>
                      <Input
                        id="workflow-name"
                        value={workflowName}
                        onChange={(e) => setWorkflowName(e.target.value)}
                        placeholder={t('workflow.enterName')}
                      />
                    </div>
                    <div>
                      <Label htmlFor="workflow-description">{t('common.description')}</Label>
                      <Textarea
                        id="workflow-description"
                        value={workflowDescription}
                        onChange={(e) => setWorkflowDescription(e.target.value)}
                        placeholder={t('workflow.enterDescription')}
                        rows={4}
                      />
                    </div>
                  </div>
                </div>
              )}

              {currentMode === 'debug' && workflowId && (
                <div className="p-6 overflow-y-auto h-full">
                  <div className="space-y-4">
                    <p className="text-muted-foreground">
                      {t('workflow.debugDescription')}
                    </p>
                    <div className="flex gap-2">
                      <Button onClick={handleExecute} variant="outline">
                        <Play className="w-4 h-4 mr-2" />
                        {t('workflow.executeWorkflow')}
                      </Button>
                      <Button variant="outline">
                        <Bug className="w-4 h-4 mr-2" />
                        {t('workflow.startDebugger')}
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </main>
        </SidebarProvider>
      </DialogContent>
    </Dialog>
  );
}