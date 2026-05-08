import { create } from 'zustand';
import type { UserConfig } from '@shared/types';

interface ConfigState {
  config: UserConfig | null;
  load: () => Promise<void>;
  save: (patch: Partial<UserConfig>) => Promise<void>;
}

export const useUserConfig = create<ConfigState>((set) => ({
  config: null,
  load: async () => {
    const cfg = await window.cflt.config.get();
    set({ config: cfg });
  },
  save: async (patch) => {
    const next = await window.cflt.config.set(patch);
    set({ config: next });
  },
}));
