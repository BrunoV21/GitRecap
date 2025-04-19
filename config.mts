
// Configuration for documentation paths and links
const config = {
  docPaths: {
    base: process.env.AiCore_GitHub || '.',
    examples: 'examples',
    observability: 'observability',
    docs: 'docs',
    config: 'config'
  },
  getDocPath: (type: string) => {
    const path = config.docPaths[type];
    if (!path) {
      throw new Error(`Invalid documentation type: ${type}`);
    }
    return `${config.docPaths.base}/${path}`;
  },
  getDocLink: (type: string, file?: string) => {
    const basePath = config.getDocPath(type);
    return file ? `${basePath}/${file}` : basePath;
  }
};

export default config;