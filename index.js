const express = require('express');
const app = express();
const PORT = process.env.PORT || 10000;

// CORS middleware
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

app.get('/', (req, res) => {
  res.json({
    message: 'SwarmForge API is running!',
    status: 'success',
    timestamp: new Date().toISOString()
  });
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// Agent activity store
const agentActivities = [];
const agentStates = {
  coordinator: { status: 'idle', currentTask: null },
  researcher: { status: 'idle', currentTask: null },
  analyzer: { status: 'idle', currentTask: null },
  executor: { status: 'idle', currentTask: null }
};

// Helper function to log activity
function logActivity(agentName, action, details = {}) {
  const activity = {
    id: Date.now() + Math.random(),
    agentName,
    action,
    details,
    timestamp: new Date().toISOString(),
    status: details.status || 'info'
  };
  agentActivities.unshift(activity);
  if (agentActivities.length > 100) agentActivities.pop();
  return activity;
}

// Agent task submission
app.post('/api/agent/task', (req, res) => {
  const { task, priority = 'medium' } = req.body;
  
  if (!task) {
    return res.status(400).json({ error: 'Task is required' });
  }

  const taskId = `task_${Date.now()}`;
  
  // Log initial activity
  logActivity('coordinator', 'task_received', { 
    taskId, 
    task, 
    priority,
    status: 'processing' 
  });

  // Simulate agent workflow
  setTimeout(() => {
    agentStates.coordinator.status = 'analyzing';
    agentStates.coordinator.currentTask = taskId;
    logActivity('coordinator', 'analyzing_task', { taskId, status: 'info' });
  }, 500);

  setTimeout(() => {
    agentStates.researcher.status = 'researching';
    agentStates.researcher.currentTask = taskId;
    logActivity('researcher', 'gathering_data', { 
      taskId, 
      sources: 3,
      status: 'info' 
    });
  }, 1500);

  setTimeout(() => {
    agentStates.analyzer.status = 'analyzing';
    agentStates.analyzer.currentTask = taskId;
    logActivity('analyzer', 'processing_data', { 
      taskId, 
      dataPoints: 47,
      status: 'info' 
    });
  }, 3000);

  setTimeout(() => {
    agentStates.executor.status = 'executing';
    agentStates.executor.currentTask = taskId;
    logActivity('executor', 'executing_plan', { taskId, status: 'info' });
  }, 4500);

  setTimeout(() => {
    agentStates.coordinator.status = 'idle';
    agentStates.coordinator.currentTask = null;
    agentStates.researcher.status = 'idle';
    agentStates.researcher.currentTask = null;
    agentStates.analyzer.status = 'idle';
    agentStates.analyzer.currentTask = null;
    agentStates.executor.status = 'idle';
    agentStates.executor.currentTask = null;
    logActivity('coordinator', 'task_complete', { 
      taskId, 
      duration: '6.2s',
      status: 'success' 
    });
  }, 6000);

  res.json({ 
    success: true, 
    taskId,
    message: 'Task submitted successfully',
    estimatedCompletion: '6 seconds'
  });
});

// Get agent activities
app.get('/api/agent/activities', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  res.json({
    activities: agentActivities.slice(0, limit),
    total: agentActivities.length
  });
});

// Get agent states
app.get('/api/agent/status', (req, res) => {
  res.json({
    agents: agentStates,
    timestamp: new Date().toISOString()
  });
});

// Simulate random agent activity
setInterval(() => {
  if (Math.random() > 0.7) {
    const agents = ['coordinator', 'researcher', 'analyzer', 'executor'];
    const actions = ['monitoring', 'idle_check', 'health_check', 'sync'];
    const agent = agents[Math.floor(Math.random() * agents.length)];
    const action = actions[Math.floor(Math.random() * actions.length)];
    logActivity(agent, action, { status: 'info', automated: true });
  }
}, 10000);


app.listen(PORT, '0.0.0.0', () => {
  console.log(`SwarmForge API running on port ${PORT}`);
});
