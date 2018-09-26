use libc::{self, c_char, c_int};
use petgraph::algo::astar;
use petgraph::graph::DiGraph;
use petgraph::Direction;
use std::ffi::CStr;
use std::mem;

const OPTIMAL_LINE_WIDTH: usize = 30;
const START_NODE_TEXT: &str = "START";
const END_NODE_TEXT: &str = "END";
const PREPOSITIONS: &[&str] = &[
    "after", "before", "for", "to", "by", "in", "on", "unto", "with", "without", "till", "from",
    "of",
];
const POSSESSIVES: &[&str] = &["your", "my", "their", "our", "his", "her"];

#[derive(Default)]
struct Node {
    pub text: String,
    pub level: usize,
    pub cost: f32,
}

impl Node {
    pub fn new(text: &str, level: usize) -> Self {
        let mut node = Self {
            text: text.to_owned(),
            level,
            cost: Default::default(),
        };
        node.cost = node.assign_cost();
        node
    }

    pub fn placeholder(text: &str, level: usize) -> Self {
        Self {
            text: text.to_owned(),
            level,
            cost: Default::default(),
        }
    }

    pub fn assign_cost(&self) -> f32 {
        Self::line_length_cost(&self.text)
            + Self::post_comma_cost(&self.text)
            + Self::post_definitive_cost(&self.text)
            + Self::post_preposition_cost(&self.text)
            + Self::post_possessive_cost(&self.text)
    }

    fn line_length_cost(text: &str) -> f32 {
        0.01 * (text.len() as f32 - OPTIMAL_LINE_WIDTH as f32).powf(2.0)
    }

    fn post_comma_cost(text: &str) -> f32 {
        if text.chars().last().expect("empty text") == ',' {
            0.0
        } else {
            1.5
        }
    }

    fn post_definitive_cost(text: &str) -> f32 {
        if text.split(' ').last().expect("empty text") == "the" {
            1.0
        } else {
            0.0
        }
    }

    fn post_preposition_cost(text: &str) -> f32 {
        if PREPOSITIONS.contains(&text.split(' ').last().expect("empty text")) {
            0.4
        } else {
            0.0
        }
    }

    fn post_possessive_cost(text: &str) -> f32 {
        if POSSESSIVES.contains(&text.split(' ').last().expect("empty text")) {
            0.2
        } else {
            0.0
        }
    }
}

struct Edge(f32);

impl Edge {
    pub fn new(cost: f32) -> Self {
        Edge(cost)
    }
}

/// Use an algorithm based on graph to layout words in the flash card.
pub fn layout(text: &str) -> Vec<String> {
    let queue = create_word_queue(text);
    let queue_len = queue.len();

    let mut graph = DiGraph::new();
    let start = graph.add_node(Node::placeholder(START_NODE_TEXT, 0));

    for (i, word) in queue.into_iter().enumerate() {
        let level = i + 1;
        let wordid = graph.add_node(Node::new(word, level));

        // lists of new nodes and edges to be added after the
        // iteration.
        let mut new_nodes = vec![];
        let mut new_edges = vec![];

        for nodeid in graph.node_indices() {
            let node = graph.node_weight(nodeid).unwrap();
            if node.level == level - 1 {
                if nodeid != start {
                    let text = [&node.text, word].join(" ");
                    let mut node_edges = vec![];
                    for predid in graph.neighbors_directed(nodeid, Direction::Incoming) {
                        let predecessor = graph.node_weight(predid).unwrap();
                        node_edges.push((predid, Edge::new(predecessor.cost)));
                    }
                    new_nodes.push((text, level, node_edges));
                }

                new_edges.push((nodeid, wordid, Edge::new(node.cost)));
            }
        }

        for node in new_nodes {
            let (text, level, edges) = node;
            let nodeid = graph.add_node(Node::new(&text, level));
            for edge in edges {
                let (predid, weight) = edge;
                graph.add_edge(predid, nodeid, weight);
            }
        }

        graph.extend_with_edges(new_edges);
    }

    let end = graph.add_node(Node::placeholder(END_NODE_TEXT, queue_len + 1));

    let mut new_edges = vec![];
    for nodeid in graph.node_indices() {
        let node = graph.node_weight(nodeid).unwrap();
        if node.level == queue_len {
            new_edges.push((nodeid, end, Edge::new(node.cost)));
        }
    }
    graph.extend_with_edges(new_edges);

    let (_, shortest_path) = astar(
        &graph,
        start,
        |node| node == end,
        |edge| edge.weight().0,
        |_| 0.0,
    ).expect("unable to find the shortest path");

    let shortest_path_len = shortest_path.len();
    shortest_path
        .into_iter()
        // Remove START node.
        .skip(1)
        // Remove END node.
        .take(shortest_path_len - 2)
        .map(|nodeid| mem::replace(&mut graph.node_weight_mut(nodeid).unwrap().text, "".into()))
        .collect()
}

fn create_word_queue<'a>(text: &'a str) -> Vec<&'a str> {
    let mut queue = vec![];
    for word in text.trim().split(' ') {
        if !word.is_empty() {
            queue.push(word);
        }
    }
    queue
}

#[repr(C)]
pub struct Line(pub libc::size_t, pub libc::size_t);

/// Creates the layout by constructing a graph and fills the given
/// buffer with (index, length) pair into the text representing the
/// lines.  Returns a non-zero value if the buffer is not big enough.
/// Returns 0 on success.
#[no_mangle]
pub unsafe fn graphlayout_layout(
    text: *const c_char,
    indicies_ptr: *mut Line,
    indicies_len: *mut libc::size_t,
) -> c_int {
    let text = CStr::from_ptr(text).to_string_lossy();
    let lines = layout(&text);
    let mut count = 0;
    let mut retcode = 0;
    for (index, len) in lines
        .iter()
        .map(|line| (text.find(line).unwrap(), line.len()))
    {
        if count < *indicies_len {
            *indicies_ptr.add(count) = Line(index, len);
            count += 1;
        } else {
            retcode = 1;
            break;
        }
    }
    *indicies_len = count;
    retcode
}
