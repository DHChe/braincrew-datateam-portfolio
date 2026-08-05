import { DashboardExplorer } from "../../components/dashboard-explorer";
import { dashboardData } from "../../lib/dashboard-data";

export default function KoreanDashboardPage() {
  return <DashboardExplorer data={dashboardData} locale="ko" />;
}
