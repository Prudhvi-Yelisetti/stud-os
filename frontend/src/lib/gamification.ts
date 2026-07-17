import { api, type GamificationProfile } from './api'

export const gamificationApi = {
  profile: () => api.get<GamificationProfile>('/gamification/profile').then((r) => r.data),
}
