import { DashboardExplorer } from "../components/dashboard-explorer";
import { dashboardData } from "../lib/dashboard-data";

export default function DashboardPage() {
  return <DashboardExplorer data={dashboardData} />;
}
