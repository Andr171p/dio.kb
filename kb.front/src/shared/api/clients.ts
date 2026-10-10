import { env } from '../config/env';
import { BackendCaller } from './backend-caller';

/** Сервисы DIOS: IAM и Media Service */
export const diosApi = new BackendCaller(env.authApiUrl);

/** Сервис базы знаний */
export const kbApi = new BackendCaller(env.kbApiUrl);
