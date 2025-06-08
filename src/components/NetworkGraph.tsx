import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface UserData {
  followers_count: number;
  following_count: number;
  is_celebrity: boolean;
  followers: string[];
  following: string[];
  profile_name?: string;
}

interface NetworkData {
  [username: string]: UserData;
}

interface Node {
  id: string;
  followers_count: number;
  following_count: number;
  is_celebrity: boolean;
  profile_name?: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface Link {
  source: string;
  target: string;
  type: 'follower' | 'following';
}

interface NetworkGraphProps {
  data: NetworkData;
}

const NetworkGraph: React.FC<NetworkGraphProps> = ({ data }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    console.log('NetworkGraph useEffect triggered with data:', data);
    if (!svgRef.current || !data) {
      console.log('Missing requirements:', { svgRef: !!svgRef.current, data: !!data });
      return;
    }

    // Clear previous graph
    d3.select(svgRef.current).selectAll("*").remove();

    // Prepare nodes and links
    const nodes: Node[] = [];
    const links: Link[] = [];
    const processedNodes = new Set<string>();

    // Create nodes
    Object.entries(data).forEach(([username, userData]) => {
      nodes.push({
        id: username,
        followers_count: userData.followers_count,
        following_count: userData.following_count,
        is_celebrity: userData.is_celebrity,
        profile_name: userData.profile_name
      });
      processedNodes.add(username);

      // Create links for followers and following
      userData.followers.forEach(follower => {
        if (!processedNodes.has(follower)) {
          const followerData = data[follower] || {
            followers_count: 0,
            following_count: 0,
            is_celebrity: false
          };
          nodes.push({
            id: follower,
            followers_count: followerData.followers_count,
            following_count: followerData.following_count,
            is_celebrity: followerData.is_celebrity,
          });
          processedNodes.add(follower);
        }
        links.push({ source: follower, target: username, type: 'follower' });
      });

      userData.following.forEach(following => {
        if (!processedNodes.has(following)) {
          const followingData = data[following] || {
            followers_count: 0,
            following_count: 0,
            is_celebrity: false
          };
          nodes.push({
            id: following,
            followers_count: followingData.followers_count,
            following_count: followingData.following_count,
            is_celebrity: followingData.is_celebrity,
          });
          processedNodes.add(following);
        }
        links.push({ source: username, target: following, type: 'following' });
      });
    });

    console.log('Processed data:', { nodes: nodes.length, links: links.length });

    // Calculate node size scale based on follower counts
    const maxFollowers = Math.max(...nodes.map(n => n.followers_count));
    const nodeSizeScale = d3.scaleSqrt()
      .domain([0, maxFollowers])
      .range([5, 30]);  // Min and max node sizes

    // Set up SVG
    const width = window.innerWidth - 40; // Adjust for padding
    const height = window.innerHeight - 100; // Adjust for header and padding
    
    console.log('Setting up SVG with dimensions:', { width, height });
    
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .style('border', '1px solid #ccc'); // Add border for debugging

    // Create a container group for zoom
    const g = svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create simulation
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))  // Increased repulsion
      .force('x', d3.forceX(width / 2).strength(0.1))  // Keep nodes centered horizontally
      .force('y', d3.forceY(height / 2).strength(0.1))  // Keep nodes centered vertically
      .force('collision', d3.forceCollide().radius((d: any) => nodeSizeScale(d.followers_count) + 5));

    // Get the main user (first user in the data)
    const mainUsername = Object.keys(data)[0];
    const mainNode = nodes.find(n => n.id === mainUsername);

    if (mainNode) {
      // Fix the main node position at the center
      mainNode.fx = width / 2;
      mainNode.fy = height / 2;

      // Style the main user's node differently
      const mainNodeRadius = nodeSizeScale(mainNode.followers_count);
      
      // Create links with gradient definitions
      const defs = g.append('defs');

      // Add a special gradient for the main node
      const mainGradient = defs.append('linearGradient')
        .attr('id', 'main-node-gradient')
        .attr('gradientUnits', 'userSpaceOnUse');

      mainGradient.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', '#4CAF50');
      mainGradient.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', '#2196F3');

      // Create a gradient for each link
      links.forEach((link, i) => {
        const gradientId = `gradient-${i}`;
        const gradient = defs.append('linearGradient')
          .attr('id', gradientId)
          .attr('gradientUnits', 'userSpaceOnUse');

        // Set gradient colors based on relationship type
        if (link.type === 'follower') {
          gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#999999');
          gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#666666');
        } else {
          gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#ff4d4d');
          gradient.append('stop')
            .attr('offset', '50%')
            .attr('stop-color', '#ff9933');
          gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#99cc00');
        }
      });

      // Create links with gradients
      const link = g.append('g')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', (d, i) => `url(#gradient-${i})`)
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 2);

      // Create nodes
      const node = g.append('g')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .call(d3.drag<any, any>()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended));

      // Add circles to nodes with special styling for main node
      node.append('circle')
        .attr('r', d => nodeSizeScale(d.followers_count))
        .attr('fill', d => d.id === mainUsername ? 'url(#main-node-gradient)' : (d.is_celebrity ? '#e74c3c' : '#3498db'))
        .attr('stroke', d => d.id === mainUsername ? '#2ecc71' : '#fff')
        .attr('stroke-width', d => d.id === mainUsername ? 3 : 1.5);

      // Add labels to nodes with special styling for main node
      node.append('text')
        .text(d => {
          if (d.profile_name) {
            return d.id === mainUsername ? 
              `${d.id} (${d.profile_name})` : 
              d.profile_name;
          }
          return d.id;
        })
        .attr('x', d => nodeSizeScale(d.followers_count) + 5)
        .attr('y', 3)
        .style('font-size', d => d.id === mainUsername ? '12px' : '10px')
        .style('font-weight', d => d.id === mainUsername ? 'bold' : 'normal')
        .style('fill', '#333');

      // Add tooltips with more detailed information
      node.append('title')
        .text(d => {
          const name = d.profile_name ? `${d.id} (${d.profile_name})` : d.id;
          return `${name}\nFollowers: ${d.followers_count}\nFollowing: ${d.following_count}`;
        });

      // Update gradient positions and links on each tick
      simulation.on('tick', () => {
        // Keep main node fixed at center
        if (mainNode) {
          mainNode.x = width / 2;
          mainNode.y = height / 2;
        }

        links.forEach((link, i) => {
          const gradientId = `gradient-${i}`;
          const gradient = d3.select(`#${gradientId}`);
          gradient
            .attr('x1', (link.source as any).x)
            .attr('y1', (link.source as any).y)
            .attr('x2', (link.target as any).x)
            .attr('y2', (link.target as any).y);
        });

        link
          .attr('x1', (d: any) => d.source.x)
          .attr('y1', (d: any) => d.source.y)
          .attr('x2', (d: any) => d.target.x)
          .attr('y2', (d: any) => d.target.y);

        node
          .attr('transform', (d: any) => `translate(${d.x},${d.y})`);
      });

      // Drag functions
      function dragstarted(event: any) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        // Don't allow dragging the main node
        if (event.subject.id !== mainUsername) {
          event.subject.fx = event.subject.x;
          event.subject.fy = event.subject.y;
        }
      }

      function dragged(event: any) {
        // Don't allow dragging the main node
        if (event.subject.id !== mainUsername) {
          event.subject.fx = event.x;
          event.subject.fy = event.y;
        }
      }

      function dragended(event: any) {
        if (!event.active) simulation.alphaTarget(0);
        // Don't allow dragging the main node
        if (event.subject.id !== mainUsername) {
          event.subject.fx = null;
          event.subject.fy = null;
        }
      }

      // Initial zoom to fit
      const bounds = (g.node() as SVGGElement).getBBox();
      const fullWidth = bounds.width;
      const fullHeight = bounds.height;
      const scale = Math.min(
        0.8,  // Maximum scale
        0.8 * Math.min(width / fullWidth, height / fullHeight)  // Scale to fit with padding
      );
      
      const transform = d3.zoomIdentity
        .translate(
          (width - fullWidth * scale) / 2 - bounds.x * scale,
          (height - fullHeight * scale) / 2 - bounds.y * scale
        )
        .scale(scale);
      
      svg.call(zoom.transform, transform);
    }

    console.log('Graph initialization complete');

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [data]);

  return (
    <div className="network-graph" style={{ width: '100%', height: 'calc(100vh - 80px)', position: 'relative' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '100%', display: 'block' }}></svg>
    </div>
  );
};

export default NetworkGraph; 