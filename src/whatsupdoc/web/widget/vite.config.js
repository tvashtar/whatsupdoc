import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [],
  build: {
    // Output directory
    outDir: '../static/widget',
    
    // Clean output directory before build
    emptyOutDir: true,
    
    // Library build configuration
    lib: {
      entry: 'src/whatsupdoc-widget.js',
      name: 'WhatsUpDocWidget',
      fileName: () => 'whatsupdoc-widget.js',
      formats: ['umd']
    },
    
    // Rollup options
    rollupOptions: {
      output: {
        // Create a regular build and a minified build
        assetFileNames: (assetInfo) => {
          return `whatsupdoc-widget.[ext]`;
        }
      }
    },
    
    // Minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    
    // Source maps for debugging
    sourcemap: true,
    
    // Target modern browsers
    target: 'es2018',
    
    // CSS options
    cssCodeSplit: false,
    
    // Chunk size warnings
    chunkSizeWarningLimit: 1000
  },
  
  // Development server options
  server: {
    port: 3000,
    open: true,
    cors: true
  },
  
  // Preview server options
  preview: {
    port: 3000,
    open: true
  },
  
  // Optimize dependencies
  optimizeDeps: {
    exclude: []
  },
  
  // Define global constants
  define: {
    __WIDGET_VERSION__: '"1.0.0"',
    __BUILD_TIME__: JSON.stringify(new Date().toISOString())
  }
});