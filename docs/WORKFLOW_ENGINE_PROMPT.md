# LangBot Workflow Engine

LangBot is an open-source platform for building instant messaging bots, especially for integrating with large language models and LLMOps platforms.

You can learn that the LangBot currently has a fixed pipeline mechanism, which is not flexible enough to meet the needs of the current business.

If user want to implement a complex business logic or entertainment scenario, they need to use the plugin system with hard code to implement the flow.

For example, 

1. Conversation with persistent memory
2. Cross-session conversation
3. Multi-modal model usage in a single query
4. Scheduled tasks
5. Multi-branch logic dependent on user input and context
6. Multi-agent collaboration

developers will use the Event Listener, Tool, Command component in plugin to implement such logic.  

Now, we consider adding a orchestratable workflow engine to the LangBot, which can be used to manage the flow of the conversation. 
And those users who are not familiar with python programming can also use the workflow engine to implement or customize the flow.

## Key Requirements

### Triggering the workflow

LangBot currently supports receiving person message and group message from QQ, WeCom, WeChat, Lark, DingTalk, Discord, Telegram, KOOK, Slack, LINE, etc.  

There're basically two types of messages:

1. Person message
2. Group message

So the workflow engine should be able to handle the message received from the person and the group.

And for some essential scenarios, the workflow should also be able to trigger by a scheduled task.

### Workflow Definition

#### Builtin Nodes

LangBot should provide some builtin nodes for the startup of the workflow engine.

1. Event-driven start node, including person message and group message.
2. Scheduled task start node, trigger by cron expression.
3. Condition node, including condition judgment and branch selection, support for multi-branch logic.
4. Action node, can be extended by the Tool component of plugin system, built-in nodes including: 
    - HTTP request: support for GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD requests.
    - Binary storage: support for storing binary data in database, please refer to the binary storage mechanism of current plugin system.
    - File storage: storing files with storage provider.
    - JSON processor: extract value from JSON, set value to JSON, serialize/deserialize JSON data.
    - Reply message: reply message to person/group message event, the event is the input of the node.
5. Variable node: set/get variable value.
6. Chat / command message branching node: branching the chat / command message based on the message content, usually judge by the prefix of the message content.
7. End node.

#### Custom Nodes

LangBot should also support custom nodes for the workflow engine.

Currently, can use the Tool component of plugin system to implement the custom nodes.
As simply receive input and output the result.

#### Workflow Variables

Provide a variable pool for the workflow engine runtime.

### On Page Debugging

LangBot should provide an on-page debugger for the workflow engine.
Built-in chat room(like the web chat of pipeline debugging) for the workflow engine, can generate the person/group message event as the input of the workflow engine.

And should support step-by-step debugging and variable value viewing.

### Export / Import Workflow

Workflow should be able to be exported as a YAML file, and be imported from a YAML file.

### Compatibility with pipeline

Pipeline and workflow should be regarded as two different concepts, pipelines' stages are fixed and can only be executed in current logic.
Workflow engine is the separate system from pipeline, and can be used to manage the flow of the conversation.

Both pipeline and workflow can be bound to bots.

## Frontend Design

Put workflow and pipeline in the same page. But different card styles and different configuration page in the detail dialog.

Use react-flow to implement the workflow engine.