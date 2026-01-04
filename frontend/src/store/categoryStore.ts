import { create } from 'zustand';
import { categoryAPI } from '../services/api';

interface Category {
  id: string;
  user_id: string;
  name: string;
  protocol: string;
  parent_id?: string;
  level: number;
  is_public: boolean;
  created_at: string;
}

interface CategoryState {
  categories: Category[];
  isLoading: boolean;
  fetchCategories: () => Promise<void>;
  createCategory: (data: { name: string; protocol: string; parent_id?: string; is_public: boolean }) => Promise<void>;
  updateCategory: (id: string, data: any) => Promise<void>;
  deleteCategory: (id: string) => Promise<void>;
}

export const useCategoryStore = create<CategoryState>((set, get) => ({
  categories: [],
  isLoading: false,

  fetchCategories: async () => {
    set({ isLoading: true });
    try {
      const response = await categoryAPI.getAll();
      set({ categories: response.data.categories, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      set({ isLoading: false });
    }
  },

  createCategory: async (data) => {
    try {
      const response = await categoryAPI.create(data);
      const newCategory = response.data.category;
      set({ categories: [...get().categories, newCategory] });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to create category');
    }
  },

  updateCategory: async (id, data) => {
    try {
      await categoryAPI.update(id, data);
      const categories = get().categories.map(cat => 
        cat.id === id ? { ...cat, ...data } : cat
      );
      set({ categories });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update category');
    }
  },

  deleteCategory: async (id) => {
    try {
      await categoryAPI.delete(id);
      set({ categories: get().categories.filter(cat => cat.id !== id) });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to delete category');
    }
  },
}));
