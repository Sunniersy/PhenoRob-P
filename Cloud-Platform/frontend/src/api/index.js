/**
 * Unified API service layer.
 *
 * Usage in View components:
 *   import { tasks, robots, dashboard } from "../api";
 *   const data = await tasks.list({ page: 1 });
 *
 * Or import individual modules:
 *   import * as tasks from "../api/tasks";
 */

import * as auth from "./auth";
import * as tasks from "./tasks";
import * as robots from "./robots";
import * as assets from "./assets";
import * as results from "./results";
import * as dashboard from "./dashboard";
import * as admin from "./admin";
import * as system from "./system";
import * as downloads from "./downloads";

export { auth, tasks, robots, assets, results, dashboard, admin, system, downloads };
