
const API_URL = "http://127.0.0.1:8000";

// Auth helpers
const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

export const login = async (email, password) => {
    const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password }),
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Login failed");
    }
    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    return data;
};

export const register = async (email, password, name) => {
    const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name }),
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Registration failed");
    }
    return response.json();
};

export const getCurrentUser = async () => {
    const response = await fetch(`${API_URL}/auth/me`, {
        headers: { ...getAuthHeader() },
    });
    if (!response.ok) return null;
    return response.json();
};

export const logout = () => {
    localStorage.removeItem('token');
};

// Campaign API
export const getCampaigns = async () => {
    const response = await fetch(`${API_URL}/campaigns`, {
        headers: { ...getAuthHeader() },
    });
    if (!response.ok) throw new Error("Failed to fetch campaigns");
    return response.json();
};

export const getCampaign = async (id) => {
    const response = await fetch(`${API_URL}/campaigns/${id}`, {
        headers: { ...getAuthHeader() },
    });
    if (!response.ok) throw new Error("Failed to fetch campaign");
    return response.json();
};

export const saveCampaign = async (name, campaignDraft) => {
    const response = await fetch(`${API_URL}/campaigns`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...getAuthHeader(),
        },
        body: JSON.stringify({ name, campaign_draft: campaignDraft }),
    });
    if (!response.ok) throw new Error("Failed to save campaign");
    return response.json();
};

export const deleteCampaign = async (id) => {
    const response = await fetch(`${API_URL}/campaigns/${id}`, {
        method: "DELETE",
        headers: { ...getAuthHeader() },
    });
    if (!response.ok) throw new Error("Failed to delete campaign");
    return response.json();
};

export const analyzeUrl = async (url) => {
    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ url }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Analysis failed");
        }

        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
};

export const publishToMeta = async (campaignDraft, pageId) => {
    try {
        const response = await fetch(`${API_URL}/meta/publish`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                campaign_draft: campaignDraft,
                page_id: pageId
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Publishing failed");
        }

        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
};

export const getMetaConfig = async () => {
    try {
        const response = await fetch(`${API_URL}/meta/config`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (!response.ok) {
            throw new Error("Failed to fetch Meta config");
        }

        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
};
