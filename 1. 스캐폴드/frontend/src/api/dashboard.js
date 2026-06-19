const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export async function fetchDashboardSummary() {
  const response = await fetch(`${API_BASE_URL}/dashboard/summary`)
  if (!response.ok) {
    throw new Error('Failed to fetch dashboard summary')
  }
  return response.json()
}
