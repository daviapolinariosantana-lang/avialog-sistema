import {env} from 'cloudflare:workers';
export function database(){if(!env.DB)throw new Error('Banco de dados indisponível.');return env.DB;}
