export interface Node {
    id: string;
    username: string;
    x?: number;
    y?: number;
    fx?: number | null;
    fy?: number | null;
}

export interface Link {
    source: string;
    target: string;
    relationship: 'follower' | 'following';
}

export interface GraphData {
    nodes: Node[];
    links: Link[];
} 