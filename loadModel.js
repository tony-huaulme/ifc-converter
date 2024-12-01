// Import required modules
const THREE = require('three');
const { GLTFLoader } = require('three-stdlib');
const fs = require('fs');
const path = require('path');

// Resolve the file path
const filePath = path.resolve(__dirname, './SORTED.glb');//zacmacosa

// Scene setup
const scene = new THREE.Scene();

// GLTFLoader instance
const loader = new GLTFLoader();

// Custom FileLoader to read the file from the filesystem
loader.manager.setURLModifier((url) => {
    // Check if the URL matches our file path
    if (url === filePath) {
        // Read the file synchronously (or asynchronously if preferred)
        const fileData = fs.readFileSync(filePath);
        const blob = new Blob([fileData]); // Create a Blob from the file data
        return URL.createObjectURL(blob); // Create an object URL for GLTFLoader
    }
    return url; // Return unmodified URLs for other resources
});

const fileData = fs.readFileSync(filePath); // Read file data
loader.parse(fileData.buffer, '', (gltf) => {
    console.log("Model loaded successfully!");
    gltf.scene.traverse((node) => {
        console.log(`${node.name}`);
    });
    scene.add(gltf.scene);
});

