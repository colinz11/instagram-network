import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { GraphData, Node, Link } from '../../types/graph';

interface NetworkGraphProps {
    data: GraphData;
    width: number;
    height: number;
}

export const NetworkGraph: React.FC<NetworkGraphProps> = ({ data, width, height }) => {
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        if (!svgRef.current || !data.nodes.length) return;

        // Clear existing SVG
        d3.select(svgRef.current).selectAll("*").remove();

        // Create the simulation
        const simulation = d3.forceSimulation<Node>(data.nodes)
            .force("link", d3.forceLink<Node, Link>(data.links)
                .id(d => d.id)
                .distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));

        // Create SVG
        const svg = d3.select(svgRef.current)
            .attr("viewBox", [0, 0, width, height]);

        // Create links
        const links = svg.append("g")
            .selectAll("line")
            .data(data.links)
            .join("line")
            .attr("stroke", d => d.relationship === 'follower' ? "#ff9999" : "#99ff99")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", 2);

        // Create nodes
        const nodes = svg.append("g")
            .selectAll<SVGGElement, Node>("g")
            .data(data.nodes)
            .join("g")
            .call(drag(simulation) as any);

        // Add circles to nodes
        nodes.append("circle")
            .attr("r", 5)
            .attr("fill", "#666");

        // Add labels to nodes
        nodes.append("text")
            .text(d => d.username)
            .attr("x", 8)
            .attr("y", 3)
            .style("font-size", "10px");

        // Update positions on each tick
        simulation.on("tick", () => {
            links
                .attr("x1", d => (d.source as unknown as Node).x!)
                .attr("y1", d => (d.source as unknown as Node).y!)
                .attr("x2", d => (d.target as unknown as Node).x!)
                .attr("y2", d => (d.target as unknown as Node).y!);

            nodes
                .attr("transform", d => `translate(${d.x},${d.y})`);
        });

        // Cleanup
        return () => {
            simulation.stop();
        };
    }, [data, width, height]);

    // Drag handler
    const drag = (simulation: d3.Simulation<Node, undefined>) => {
        function dragstarted(event: any) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event: any) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event: any) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }

        return d3.drag<SVGGElement, Node>()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);
    };

    return (
        <svg
            ref={svgRef}
            width={width}
            height={height}
            style={{ border: '1px solid #ccc' }}
        />
    );
}; 