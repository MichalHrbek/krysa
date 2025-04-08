export type MachineType = {
	id: string;
	version: number;
	connections: Record<string, number[]>;
	connected: boolean;
	sudostealer: SudostealerType;
	persistence: PersistenceType;
	specs: any;
};

type SudostealerType = {
	enabled: boolean;
	credentials: Array<string>;
}

type PersistenceType = {
	enabled: boolean;
	credentials: Array<string>;
}