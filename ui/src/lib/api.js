import {
    agentState,
    internet,
    modelList,
    projectList,
    messages,
    projectFiles,
    searchEngineList,
} from "./store";
import { io } from "socket.io-client";


const getApiBaseUrl = () => {
    if (typeof window !== 'undefined') {
        const host = window.location.hostname;
        if (host === 'localhost' || host === '127.0.0.1') {
            return 'http://127.0.0.1:1337';
        } else {
            return `http://${host}:1337`;
        }
    } else {
        return 'http://127.0.0.1:1337';
    }
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || getApiBaseUrl();
export const socket = io(API_BASE_URL, { autoConnect: false });

export async function checkServerStatus() {
    return new Promise((resolve, reject) => {
        socket.emit('check_status');  // Emit the event to check status

        socket.on('status_response', (status) => {
            resolve(status);  // Resolve the status result
        });

        socket.on('status_error', (error) => {
            console.error('Error checking server status:', error);
            reject(error);  // Reject if there's an error
        });
    });
}


export async function fetchInitialData() {
    return new Promise((resolve, reject) => {
        socket.emit('fetch_initial_data');  // Emit WebSocket event to request initial data

        // Listen for the response
        socket.on('initial_data_response', (data) => {
            projectList.set(data.projects);
            modelList.set(data.models);
            searchEngineList.set(data.search_engines);
            localStorage.setItem("defaultData", JSON.stringify(data));
            resolve(data);  // Resolve the Promise
        });

        // Handle errors
        socket.on('initial_data_error', (error) => {
            console.error('Error fetching initial data:', error);
            reject(error);  // Reject the Promise
        });
    });
}


export async function createProject(projectName) {
    return new Promise((resolve, reject) => {
        socket.emit('create_project', { project_name: projectName });

        socket.on('create_project_success', () => {
            projectList.update((projects) => [...projects, projectName]);
            resolve();
        });

        socket.on('create_project_error', (error) => {
            console.error('Error creating project:', error);
            reject(error);
        });
    });
}


export async function deleteProject(projectName) {
    return new Promise((resolve, reject) => {
        socket.emit('delete_project', { project_name: projectName });

        socket.on('delete_project_success', () => {
            resolve();
        });

        socket.on('delete_project_error', (error) => {
            console.error('Error deleting project:', error);
            reject(error);
        });
    });
}


// Fetch messages (formerly /api/messages)
export async function fetchMessages() {
    return new Promise((resolve, reject) => {
        const projectName = localStorage.getItem("selectedProject");
        socket.emit('fetch_messages', { project_name: projectName });

        socket.on('fetch_messages_response', (data) => {
            messages.set(data.messages);
            resolve(data.messages);
        });

        socket.on('fetch_messages_error', (error) => {
            console.error('Error fetching messages:', error);
            reject(error);
        });
    });
}

// Fetch agent state (formerly /api/get-agent-state)
export async function fetchAgentState() {
    return new Promise((resolve, reject) => {
        const projectName = localStorage.getItem("selectedProject");
        socket.emit('get_agent_state', { project_name: projectName });

        socket.on('get_agent_state_response', (data) => {
            agentState.set(data.state);
            resolve(data.state);
        });

        socket.on('get_agent_state_error', (error) => {
            console.error('Error fetching agent state:', error);
            reject(error);
        });
    });
}

// Execute agent (formerly /api/execute-agent)
export async function executeAgent(prompt) {
    return new Promise((resolve, reject) => {
        const projectName = localStorage.getItem("selectedProject");
        const modelId = localStorage.getItem("selectedModel");

        if (!modelId) {
            alert("Please select the LLM model first.");
            return reject("No model selected");
        }

        socket.emit('user_message', {
            prompt: prompt,
            base_model: modelId,
            project_name: projectName,
        });

        // Optionally listen for a response or wait for the task to complete.
        socket.on('user_message_success', () => {
            fetchMessages().then(resolve).catch(reject);
        });

        socket.on('user_message_error', (error) => {
            console.error('Error executing agent:', error);
            reject(error);
        });
    });
}

// Get browser snapshot (formerly /api/browser-snapshot)
export async function getBrowserSnapshot(snapshotPath) {
    return new Promise((resolve, reject) => {
        socket.emit('get_browser_snapshot', { snapshot_path: snapshotPath });

        socket.on('get_browser_snapshot_response', (data) => {
            resolve(data.snapshot);
        });

        socket.on('get_browser_snapshot_error', (error) => {
            console.error('Error fetching browser snapshot:', error);
            reject(error);
        });
    });
}

// Fetch project files (formerly /api/get-project-files)
export async function fetchProjectFiles() {
    return new Promise((resolve, reject) => {
        const projectName = localStorage.getItem("selectedProject");
        socket.emit('get_project_files', { project_name: projectName });

        socket.on('get_project_files_response', (data) => {
            projectFiles.set(data.files);
            resolve(data.files);
        });

        socket.on('get_project_files_error', (error) => {
            console.error('Error fetching project files:', error);
            reject(error);
        });
    });
}

// Check internet status (you can keep this as it doesn't interact with the server)
export async function checkInternetStatus() {
    if (navigator.onLine) {
        internet.set(true);
    } else {
        internet.set(false);
    }
}

// Fetch settings (formerly /api/settings)
export async function fetchSettings() {
    return new Promise((resolve, reject) => {
        socket.emit('get_settings');

        socket.on('get_settings_response', (data) => {
            resolve(data.settings);
        });

        socket.on('get_settings_error', (error) => {
            console.error('Error fetching settings:', error);
            reject(error);
        });
    });
}

// Update settings (formerly /api/settings)
export async function updateSettings(settings) {
    return new Promise((resolve, reject) => {
        socket.emit('set_settings', settings);

        socket.on('set_settings_response', (data) => {
            resolve(data.message);
        });

        socket.on('set_settings_error', (error) => {
            console.error('Error updating settings:', error);
            reject(error);
        });
    });
}

// Fetch logs (formerly /api/logs)
export async function fetchLogs() {
    return new Promise((resolve, reject) => {
        socket.emit('fetch_logs');

        socket.on('fetch_logs_response', (data) => {
            resolve(data.logs);
        });

        socket.on('fetch_logs_error', (error) => {
            console.error('Error fetching logs:', error);
            reject(error);
        });
    });
}