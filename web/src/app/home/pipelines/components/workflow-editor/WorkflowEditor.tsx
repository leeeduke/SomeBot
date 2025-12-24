'use client';

import React, { useState, useCallback, useEffect } from 'react';
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
  Edge,
  BackgroundVariant,
  Panel,
  NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Save, X, Play } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useTranslation } from 'react-i18next';
import { httpClient } from '@/app/infra/http/HttpClient';
import { extractI18nObject } from '@/i18n/I18nProvider';
import { useTheme } from 'next-themes';
import NodePalette from './NodePalette';
import NodeConfigPanel from './NodeConfigPanel';
import CustomNode from './CustomNode';

interface WorkflowEditorProps {
  workflow: any;
  onSave: () => void;
  onClose: () => void;
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

interface CustomNodeData {
  label: string;
  type: string;
  config?: Record<string, any>;
  description?: string;
  [key: string]: unknown;
}

type WorkflowNode = Node<CustomNodeData>;
type WorkflowEdge = Edge<{ condition?: any }>;

// Define custom node types
const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

export default function WorkflowEditor({ workflow, onSave, onClose }: WorkflowEditorProps) {
  const { toast } = useToast();
  const { t } = useTranslation();
  const { resolvedTheme } = useTheme();
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<WorkflowEdge>([]);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [workflowName, setWorkflowName] = useState(workflow.name);
  const [workflowDescription] = useState(workflow.description || '');
  const [isSaving, setIsSaving] = useState(false);
  const [nodeManifests, setNodeManifests] = useState<Record<string, NodeManifest>>({});

  const isDark = resolvedTheme === 'dark';

  useEffect(() => {
    // Load node manifests and workflow data
    loadNodeManifests();
    loadWorkflow();
  }, [workflow.id]);

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
      const data = await httpClient.getWorkflow(workflow.id);
      const workflowData = data.workflow;

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
          position: node.position || { x: 100, y: 100 },
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
      toast({
        title: t('common.error'),
        description: t('workflow.loadFailed'),
        variant: 'destructive',
      });
    }
  };

  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge: WorkflowEdge = {
        ...params,
        id: `edge-${Date.now()}`,
        type: 'smoothstep',
        source: params.source ?? '',
        target: params.target ?? '',
      };
      setEdges((eds) => addEdge(newEdge, eds) as WorkflowEdge[]);
    },
    [setEdges]
  );

  const onNodeClick = useCallback((_: any, node: WorkflowNode) => {
    setSelectedNode(node);
  }, []);

  const onNodeDragStop = useCallback(
    (_: any, node: WorkflowNode) => {
      // Update node position
      const updatedNodes = nodes.map((n) =>
        n.id === node.id ? { ...n, position: node.position } : n
      );
      setNodes(updatedNodes);
    },
    [nodes, setNodes]
  );

  const handleAddNode = (nodeType: string) => {
    // Get the manifest for this node type
    const manifest = nodeManifests[nodeType];

    // Use localized label from manifest, fallback to hardcoded label
    let label = `New ${nodeType} Node`;
    if (manifest && manifest.label) {
      label = extractI18nObject(manifest.label);
    }

    const newNode: WorkflowNode = {
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
          : node
      )
    );
  };

  const handleDeleteNode = (nodeId: string) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    setSelectedNode(null);
  };

  const handleSave = async () => {
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

      await httpClient.updateWorkflow(workflow.id, {
        name: workflowName,
        description: workflowDescription,
        nodes: workflowNodes,
        edges: workflowEdges,
      });

      toast({
        title: t('common.success'),
        description: t('workflow.saveSuccess'),
      });
      onSave();
    } catch (error) {
      console.error('Error saving workflow:', error);
      toast({
        title: t('common.error'),
        description: t('workflow.saveError'),
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleExecute = async () => {
    try {
      const data = await httpClient.executeWorkflow(workflow.id, {
        trigger: 'manual',
        trigger_data: {},
      });

      toast({
        title: t('common.success'),
        description: t('workflow.executeSuccess', { id: data.execution_id }),
      });
    } catch (error) {
      console.error('Error executing workflow:', error);
      toast({
        title: t('common.error'),
        description: t('workflow.executeFailed'),
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="h-[80vh] flex">
      {/* Left Sidebar - Node Palette */}
      <div className="w-64 border-r bg-background p-4 overflow-hidden">
        <NodePalette onAddNode={handleAddNode} />
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onNodeDragStop={onNodeDragStop}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={12}
            size={1}
            color={isDark ? '#4b5563' : '#d1d5db'}
          />
          <MiniMap />
          <Controls />

          {/* Top Panel - Workflow Info and Actions */}
          <Panel position="top-left" className="flex gap-2 items-center bg-background p-2 rounded-lg shadow-md">
            <Input
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              placeholder={t('workflow.workflowName')}
              className="w-48"
            />
            <Button
              onClick={handleSave}
              disabled={isSaving}
              size="sm"
              className="flex items-center gap-1"
            >
              <Save className="w-4 h-4" />
              {isSaving ? t('common.saving') : t('common.save')}
            </Button>
            <Button
              onClick={handleExecute}
              size="sm"
              variant="secondary"
              className="flex items-center gap-1"
            >
              <Play className="w-4 h-4" />
              {t('workflow.execute')}
            </Button>
            <Button
              onClick={onClose}
              size="sm"
              variant="ghost"
              className="flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              {t('common.close')}
            </Button>
          </Panel>
        </ReactFlow>
      </div>

      {/* Right Sidebar - Node Configuration */}
      {selectedNode && (
        <div className="w-80 border-l bg-background">
          <NodeConfigPanel
            node={selectedNode}
            onUpdate={(updates) => handleUpdateNode(selectedNode.id, updates)}
            onDelete={() => handleDeleteNode(selectedNode.id)}
            onClose={() => setSelectedNode(null)}
          />
        </div>
      )}
    </div>
  );
}