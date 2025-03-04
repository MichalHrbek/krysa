export type MachineType = {
	id: string;
	version: number;
	connections: Record<string, number[]>;
	connected: boolean;
};