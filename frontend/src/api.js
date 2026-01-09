
const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const login = async (email, password) => {
    const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: 'include',
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Login failed");
    }
    return response.json();
};

export const register = async (email, password, name) => {
    const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name }),
        credentials: 'include',
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Registration failed");
    }
    return response.json();
};

export const getCurrentUser = async () => {
    const response = await fetch(`${API_URL}/auth/me`, {
        credentials: 'include',
    });
    if (!response.ok) return null;
    return response.json();
};

export const logout = async () => {
    await fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        credentials: 'include',
    });
};

// Campaign API
export const getCampaigns = async () => {
    const response = await fetch(`${API_URL}/campaigns`, {
        credentials: 'include',
    });
    if (!response.ok) throw new Error("Failed to fetch campaigns");
    return response.json();
};

export const getCampaign = async (id) => {
    const response = await fetch(`${API_URL}/campaigns/${id}`, {
        credentials: 'include',
    });
    if (!response.ok) throw new Error("Failed to fetch campaign");
    return response.json();
};

export const saveCampaign = async (name, campaignDraft) => {
    const response = await fetch(`${API_URL}/campaigns`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, campaign_draft: campaignDraft }),
        credentials: 'include',
    });
    if (!response.ok) throw new Error("Failed to save campaign");
    return response.json();
};

export const deleteCampaign = async (id) => {
    const response = await fetch(`${API_URL}/campaigns/${id}`, {
        method: "DELETE",
        credentials: 'include',
    });
    if (!response.ok) throw new Error("Failed to delete campaign");
    return response.json();
};

export const analyzeUrl = async (url) => {
    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url }),
            credentials: 'include',
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Analysis failed");
        }

        return await response.json();
    } catch (error) {
        throw error;
    }
};

export const publishToMeta = async (campaignDraft, pageId) => {
    try {
        const response = await fetch(`${API_URL}/meta/publish`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                campaign_draft: campaignDraft,
                page_id: pageId
            }),
            credentials: 'include',
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Publishing failed");
        }

        return await response.json();
    } catch (error) {
        throw error;
    }
};

export const getMetaConfig = async () => {
    try {
        const response = await fetch(`${API_URL}/meta/config`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
            credentials: 'include',
        });

        if (!response.ok) {
            throw new Error("Failed to fetch Meta config");
        }

        return await response.json();
    } catch (error) {
        throw error;
    }
};
