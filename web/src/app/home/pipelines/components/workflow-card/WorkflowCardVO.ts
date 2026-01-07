export class WorkflowCardVO {
  name: string;
  description: string;
  id: string;
  lastUpdatedTimeAgo: string;
  status: 'draft' | 'active' | 'inactive' | 'archived';
  triggerTypes: string[];

  constructor(data: {
    name: string;
    description: string;
    id: string;
    lastUpdatedTimeAgo: string;
    status: 'draft' | 'active' | 'inactive' | 'archived';
    triggerTypes: string[];
  }) {
    this.name = data.name;
    this.description = data.description;
    this.id = data.id;
    this.lastUpdatedTimeAgo = data.lastUpdatedTimeAgo;
    this.status = data.status;
    this.triggerTypes = data.triggerTypes;
  }
}