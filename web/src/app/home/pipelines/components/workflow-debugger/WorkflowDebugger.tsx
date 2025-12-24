'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Play, Pause, StepForward, RotateCcw, Bug, CheckCircle, XCircle, Clock } from 'lucide-react';
import { toast } from 'sonner';

interface WorkflowDebuggerProps {
  workflowId: string;
  onClose?: () => void;
}

interface DebugNode {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped';
  output?: any;
  error?: string;
}

interface DebugSession {
  executionId: string;
  status: string;
  nodes: DebugNode[];
  variables: Record<string, any>;
  currentNode?: string;
  errors: any[];
}

export default function WorkflowDebugger({ workflowId, onClose }: WorkflowDebuggerProps) {
  const [debugSession, setDebugSession] = useState<DebugSession | null>(null);
  const [breakpoints, setBreakpoints] = useState<Set<string>>(new Set());
  const [stepMode, setStepMode] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [executionLogs, setExecutionLogs] = useState<string[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const handleStartDebug = async () => {
    setIsRunning(true);
    setExecutionLogs(['Starting debug session...']);

    try {
      const response = await fetch(`/v1/workflow/debug/${workflowId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          trigger: 'manual',
          trigger_data: {},
          breakpoints: Array.from(breakpoints),
          step_mode: stepMode,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start debug session');
      }

      const data = await response.json();

      setDebugSession({
        executionId: data.data.execution_id,
        status: data.data.status,
        nodes: data.data.executed_nodes.map((nodeId: string) => ({
          id: nodeId,
          name: nodeId,
          status: 'success',
        })),
        variables: data.data.final_variables || {},
        errors: data.data.errors || [],
      });

      setExecutionLogs(prev => [
        ...prev,
        `Debug session started. Execution ID: ${data.data.execution_id}`,
        ...data.data.executed_nodes.map((n: string) => `✓ Node executed: ${n}`),
      ]);

      if (data.data.errors && data.data.errors.length > 0) {
        data.data.errors.forEach((error: any) => {
          setExecutionLogs(prev => [...prev, `✗ Error in ${error.node_id}: ${error.error}`]);
        });
      }

      toast.success('Debug session completed');
    } catch (error) {
      console.error('Error starting debug session:', error);
      toast.error('Failed to start debug session');
      setExecutionLogs(prev => [...prev, `✗ Error: ${error}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleStepForward = () => {
    setExecutionLogs(prev => [...prev, 'Step forward...']);
    // In a real implementation, this would step through the workflow
  };

  const handleReset = () => {
    setDebugSession(null);
    setExecutionLogs([]);
    setSelectedNode(null);
    setIsRunning(false);
    setIsPaused(false);
  };

  const toggleBreakpoint = (nodeId: string) => {
    const newBreakpoints = new Set(breakpoints);
    if (newBreakpoints.has(nodeId)) {
      newBreakpoints.delete(nodeId);
    } else {
      newBreakpoints.add(nodeId);
    }
    setBreakpoints(newBreakpoints);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'running':
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'skipped':
        return <Clock className="w-4 h-4 text-gray-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Debug Controls */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Bug className="w-5 h-5" />
            Workflow Debugger
          </CardTitle>
          <CardDescription>
            Debug and test your workflow execution step by step
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Button
              onClick={handleStartDebug}
              disabled={isRunning}
              variant={isRunning ? 'secondary' : 'default'}
              size="sm"
            >
              {isRunning ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Start Debug
                </>
              )}
            </Button>

            <Button
              onClick={handleStepForward}
              disabled={!isRunning || !stepMode}
              variant="outline"
              size="sm"
            >
              <StepForward className="w-4 h-4 mr-2" />
              Step
            </Button>

            <Button
              onClick={handleReset}
              variant="outline"
              size="sm"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>

            <div className="ml-auto flex items-center gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={stepMode}
                  onChange={(e) => setStepMode(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Step Mode</span>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Debug Information */}
      <div className="flex-1 grid grid-cols-3 gap-4">
        {/* Execution Flow */}
        <Card className="col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Execution Flow</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[400px]">
              <div className="p-4 space-y-2">
                {debugSession?.nodes.map((node) => (
                  <div
                    key={node.id}
                    className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-accent ${
                      selectedNode === node.id ? 'bg-accent' : ''
                    }`}
                    onClick={() => setSelectedNode(node.id)}
                  >
                    {getStatusIcon(node.status)}
                    <span className="text-sm flex-1">{node.name}</span>
                    {breakpoints.has(node.id) && (
                      <Badge variant="outline" className="text-xs">BP</Badge>
                    )}
                  </div>
                )) || (
                  <p className="text-muted-foreground text-sm">
                    No execution data yet. Start debugging to see the flow.
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Variables & Output */}
        <Card className="col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Variables</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[400px]">
              <div className="p-4">
                {debugSession && Object.keys(debugSession.variables).length > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(debugSession.variables).map(([key, value]) => (
                      <div key={key} className="space-y-1">
                        <div className="font-mono text-sm font-medium">{key}</div>
                        <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-sm">
                    No variables set yet.
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Execution Logs */}
        <Card className="col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Execution Logs</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[400px]">
              <div className="p-4">
                {executionLogs.length > 0 ? (
                  <div className="space-y-1">
                    {executionLogs.map((log, index) => (
                      <div
                        key={index}
                        className={`text-xs font-mono ${
                          log.startsWith('✓')
                            ? 'text-green-600'
                            : log.startsWith('✗')
                            ? 'text-red-600'
                            : 'text-muted-foreground'
                        }`}
                      >
                        {log}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-sm">
                    No logs yet. Start debugging to see execution logs.
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Errors Panel */}
      {debugSession && debugSession.errors.length > 0 && (
        <Card className="mt-4">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-red-600">Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {debugSession.errors.map((error, index) => (
                <div key={index} className="p-2 bg-red-50 dark:bg-red-900/20 rounded">
                  <div className="font-medium text-sm">{error.node_id || 'Unknown Node'}</div>
                  <div className="text-xs text-muted-foreground">{error.error}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}