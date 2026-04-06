import type { FC } from "react";
import CommonAgentArea from "./common-agent-area";

import type { AgentViewProps } from "@/types/agent";

const AShareAgentArea: FC<AgentViewProps> = ({ agentName }) => {
  return <CommonAgentArea agentName={agentName} />;
};

export default AShareAgentArea;
