import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
export default defineConfig({root:'portable',publicDir:'../public',plugins:[react()],resolve:{alias:{'@':path.resolve(import.meta.dirname)}},build:{outDir:'../portable-dist',emptyOutDir:true,target:'es2022'}});
