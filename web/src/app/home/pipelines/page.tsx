'use client';
import { useState, useEffect } from 'react';
import CreateCardComponent from '@/app/infra/basic-component/create-card-component/CreateCardComponent';
import { httpClient } from '@/app/infra/http/HttpClient';
import { PipelineCardVO } from '@/app/home/pipelines/components/pipeline-card/PipelineCardVO';
import PipelineCard from '@/app/home/pipelines/components/pipeline-card/PipelineCard';
import WorkflowCard from '@/app/home/pipelines/components/workflow-card/WorkflowCard';
import { WorkflowCardVO } from '@/app/home/pipelines/components/workflow-card/WorkflowCardVO';
import styles from './pipelineConfig.module.css';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';
import PipelineDialog from './PipelineDetailDialog';
import WorkflowDetailDialog from './WorkflowDetailDialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { GitBranch, Layers } from 'lucide-react';

export default function PluginConfigPage() {
  const { t } = useTranslation();
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);
  const [workflowDialogOpen, setWorkflowDialogOpen] = useState<boolean>(false);
  const [selectionDialogOpen, setSelectionDialogOpen] = useState<boolean>(false);
  const [isEditForm, setIsEditForm] = useState(false);
  const [pipelineList, setPipelineList] = useState<PipelineCardVO[]>([]);
  const [workflowList, setWorkflowList] = useState<WorkflowCardVO[]>([]);
  const [selectedPipelineId, setSelectedPipelineId] = useState('');
  const [selectedWorkflowId, setSelectedWorkflowId] = useState('');
  const [sortByValue, setSortByValue] = useState<string>('created_at');
  const [sortOrderValue, setSortOrderValue] = useState<string>('DESC');

  useEffect(() => {
    // Load sort preference from localStorage
    const savedSortBy = localStorage.getItem('pipeline_sort_by');
    const savedSortOrder = localStorage.getItem('pipeline_sort_order');

    if (savedSortBy && savedSortOrder) {
      setSortByValue(savedSortBy);
      setSortOrderValue(savedSortOrder);
      getPipelines(savedSortBy, savedSortOrder);
      getWorkflows();
    } else {
      getPipelines();
      getWorkflows();
    }
  }, []);

  function getPipelines(
    sortBy: string = sortByValue,
    sortOrder: string = sortOrderValue,
  ) {
    httpClient
      .getPipelines(sortBy, sortOrder)
      .then((value) => {
        const currentTime = new Date();
        const pipelineList = value.pipelines.map((pipeline) => {
          const lastUpdatedTimeAgo = Math.floor(
            (currentTime.getTime() -
              new Date(
                pipeline.updated_at ?? currentTime.getTime(),
              ).getTime()) /
              1000 /
              60 /
              60 /
              24,
          );

          const lastUpdatedTimeAgoText =
            lastUpdatedTimeAgo > 0
              ? ` ${lastUpdatedTimeAgo} ${t('pipelines.daysAgo')}`
              : t('pipelines.today');

          return new PipelineCardVO({
            lastUpdatedTimeAgo: lastUpdatedTimeAgoText,
            description: pipeline.description,
            id: pipeline.uuid ?? '',
            name: pipeline.name,
            isDefault: pipeline.is_default ?? false,
          });
        });
        setPipelineList(pipelineList);
      })
      .catch((error) => {
        toast.error(t('pipelines.getPipelineListError') + error.message);
      });
  }

  function getWorkflows() {
    httpClient
      .getWorkflows()
      .then((data) => {
        if (data.workflows) {
          const currentTime = new Date();
          const workflowList = data.workflows.map((workflow: any) => {
            const lastUpdatedTimeAgo = Math.floor(
              (currentTime.getTime() -
                new Date(
                  workflow.updated_at ?? currentTime.getTime(),
                ).getTime()) /
                1000 /
                60 /
                60 /
                24,
            );

            const lastUpdatedTimeAgoText =
              lastUpdatedTimeAgo > 0
                ? ` ${lastUpdatedTimeAgo} ${t('pipelines.daysAgo')}`
                : t('pipelines.today');

            return new WorkflowCardVO({
              lastUpdatedTimeAgo: lastUpdatedTimeAgoText,
              description: workflow.description || '',
              id: workflow.id,
              name: workflow.name,
              status: workflow.status,
              triggerTypes: workflow.trigger_types || [],
            });
          });
          setWorkflowList(workflowList);
        }
      })
      .catch((error) => {
        console.error('Error fetching workflows:', error);
      });
  }

  const handlePipelineClick = (pipelineId: string) => {
    setSelectedPipelineId(pipelineId);
    setIsEditForm(true);
    setDialogOpen(true);
  };

  const handleWorkflowClick = (workflowId: string) => {
    setSelectedWorkflowId(workflowId);
    setIsEditForm(true);
    setWorkflowDialogOpen(true);
  };

  const handleCreateNew = () => {
    setSelectionDialogOpen(true);
  };

  const handleCreatePipeline = () => {
    setSelectionDialogOpen(false);
    setIsEditForm(false);
    setSelectedPipelineId('');
    setDialogOpen(true);
  };

  const handleCreateWorkflow = () => {
    setSelectionDialogOpen(false);
    setIsEditForm(false);
    setSelectedWorkflowId('');
    setWorkflowDialogOpen(true);
  };

  function handleSortChange(value: string) {
    const [newSortBy, newSortOrder] = value.split(',').map((s) => s.trim());
    setSortByValue(newSortBy);
    setSortOrderValue(newSortOrder);

    // Save sort preference to localStorage
    localStorage.setItem('pipeline_sort_by', newSortBy);
    localStorage.setItem('pipeline_sort_order', newSortOrder);

    getPipelines(newSortBy, newSortOrder);
  }

  return (
    <div className={styles.configPageContainer}>
      <PipelineDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        pipelineId={selectedPipelineId || undefined}
        isEditMode={isEditForm}
        onFinish={() => {
          getPipelines();
        }}
        onNewPipelineCreated={(pipelineId) => {
          getPipelines();
          setSelectedPipelineId(pipelineId);
          setIsEditForm(true);
          setDialogOpen(true);
        }}
        onDeletePipeline={() => {
          getPipelines();
          setDialogOpen(false);
        }}
        onCancel={() => {
          setDialogOpen(false);
        }}
      />

      <WorkflowDetailDialog
        open={workflowDialogOpen}
        onOpenChange={setWorkflowDialogOpen}
        workflowId={selectedWorkflowId || undefined}
        isEditMode={isEditForm}
        onFinish={() => {
          getWorkflows();
        }}
        onNewWorkflowCreated={(workflowId: string) => {
          getWorkflows();
          setSelectedWorkflowId(workflowId);
          setIsEditForm(true);
          setWorkflowDialogOpen(true);
        }}
        onDeleteWorkflow={() => {
          getWorkflows();
          setWorkflowDialogOpen(false);
        }}
        onCancel={() => {
          setWorkflowDialogOpen(false);
        }}
      />

      <Dialog open={selectionDialogOpen} onOpenChange={setSelectionDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t('pipelines.createNewTitle')}</DialogTitle>
            <DialogDescription>
              {t('pipelines.createNewDescription')}
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <Button
              variant="outline"
              className="h-32 flex-col gap-3"
              onClick={handleCreatePipeline}
            >
              <Layers className="h-8 w-8" />
              <div className="text-center">
                <div className="font-semibold">{t('pipelines.pipeline')}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {t('pipelines.pipelineDescription')}
                </div>
              </div>
            </Button>
            <Button
              variant="outline"
              className="h-32 flex-col gap-3"
              onClick={handleCreateWorkflow}
            >
              <GitBranch className="h-8 w-8" />
              <div className="text-center">
                <div className="font-semibold">{t('pipelines.workflow')}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {t('pipelines.workflowDescription')}
                </div>
              </div>
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <div className="w-full">
        <div className="flex flex-row justify-end items-center mb-4 px-[0.8rem]">
          <Select
            value={`${sortByValue},${sortOrderValue}`}
            onValueChange={handleSortChange}
          >
            <SelectTrigger className="w-[180px] cursor-pointer bg-[#ffffff] dark:bg-[#2a2a2e]">
              <SelectValue placeholder={t('pipelines.sortBy')} />
            </SelectTrigger>
            <SelectContent className="bg-[#ffffff] dark:bg-[#2a2a2e]">
              <SelectItem
                value="created_at,DESC"
                className="text-gray-900 dark:text-gray-100"
              >
                {t('pipelines.newestCreated')}
              </SelectItem>
              <SelectItem
                value="created_at,ASC"
                className="text-gray-900 dark:text-gray-100"
              >
                {t('pipelines.earliestCreated')}
              </SelectItem>
              <SelectItem
                value="updated_at,DESC"
                className="text-gray-900 dark:text-gray-100"
              >
                {t('pipelines.recentlyEdited')}
              </SelectItem>
              <SelectItem
                value="updated_at,ASC"
                className="text-gray-900 dark:text-gray-100"
              >
                {t('pipelines.earliestEdited')}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className={styles.pipelineListContainer}>
          <CreateCardComponent
            width={'100%'}
            height={'10rem'}
            plusSize={'90px'}
            onClick={handleCreateNew}
          />

          {pipelineList.map((pipeline) => {
            return (
              <div
                key={`pipeline-${pipeline.id}`}
                onClick={() => handlePipelineClick(pipeline.id)}
              >
                <PipelineCard cardVO={pipeline} />
              </div>
            );
          })}

          {workflowList.map((workflow) => {
            return (
              <div
                key={`workflow-${workflow.id}`}
                onClick={() => handleWorkflowClick(workflow.id)}
              >
                <WorkflowCard cardVO={workflow} />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}