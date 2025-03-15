// server.js
const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
require("dotenv").config(); // Load environment variables

const app = express();
app.use(express.json());

// CORS Configuration - VERY IMPORTANT
const allowedOrigins = ['http://localhost:5000', 'http://127.0.0.1:5000'];

const corsOptions = {
    origin: function (origin, callback) {
        if (allowedOrigins.indexOf(origin) !== -1 || !origin) { // allow requests with no origin
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    credentials: true, // If you need to send cookies, set this to true
    optionsSuccessStatus: 200 // Some legacy browsers choke on 204
};

app.use(cors(corsOptions));

// MongoDB Atlas Connection (Using Environment Variable)
const USER2_DB_URI = process.env.USER2_DB_URI; // Separate database for user details
const JWT_SECRET = process.env.JWT_SECRET || "supersecretkey";

if (!USER2_DB_URI) {
    console.error("Error: USER2_DB_URI is not defined. Check your .env file.");
    process.exit(1);
}

// Connect to user details database
const userDB = mongoose.createConnection(USER2_DB_URI);
userDB.on("connected", () => console.log("Connected to users2 database"));
userDB.on("error", (err) => console.error("User2 DB connection error:", err));

// User Schema in users2 database
const UserSchema = new mongoose.Schema({
    username: { type: String, required: true },
    email: { type: String, unique: true, required: true },
    password: { type: String, required: true },
});
const User = userDB.model("User", UserSchema, "users2"); // Ensuring the collection name is users2

// Test Route to Check Server Status
app.get("/", (req, res) => {
    res.send("Server is running!");
});

// Signup Route
app.post("/signup", async (req, res) => {
    try {
        console.log("Signup request received:", req.body);
        const { username, email, password } = req.body;
        if (!username || !email || !password) {
            return res.status(400).json({ error: "All fields are required" });
        }

        if (await User.findOne({ email })) {
            console.log("User already exists");
            return res.status(400).json({ error: "User already exists" });
        }

        const hashedPassword = await bcrypt.hash(password, 10);
        const user = new User({ username, email, password: hashedPassword });
        await user.save();
        res.status(201).json({ message: "User registered successfully" });
    } catch (error) {
        console.error("Signup error:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// Login Route
app.post("/login", async (req, res) => {
    try {
        console.log("Login request received:", req.body);
        const { email, password } = req.body;
        if (!email || !password) {
            return res.status(400).json({ error: "All fields are required" });

        }

        const user = await User.findOne({ email });
        if (!user || !(await bcrypt.compare(password, user.password))) {
            console.log("Invalid login attempt");
            return res.status(401).json({ error: "Invalid email or password" });
        }

        // Generate JWT token
        const token = jwt.sign({ userId: user._id, email: user.email }, JWT_SECRET, { expiresIn: "1h" });
        res.json({ message: "Login successful", token });
    } catch (error) {
        console.error("Login error:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// Authenticated Route Example
app.get("/profile", async (req, res) => {
    try {
        const token = req.headers.authorization?.split(" ")[1];
        if (!token) {
            return res.status(401).json({ error: "Unauthorized" });
        }

        // Use jwt.verify with a callback
        jwt.verify(token, JWT_SECRET, async (err, decoded) => {
            if (err) {
                console.error("Invalid token:", err);
                return res.status(401).json({ error: "Invalid token" });
            }

            try {
                const user = await User.findById(decoded.userId).select("-password");
                if (!user) {
                    return res.status(404).json({ error: "User not found" });
                }

                res.json(user); // Send user data (excluding password)
            } catch (error) {
                console.error("Error fetching user:", error);
                return res.status(500).json({ error: "Internal Server Error" });
            }
        });
    } catch (error) {
        console.error("Profile error:", error);
        res.status(401).json({ error: "Invalid token" });
    }
});

// Updated Port Handling to Avoid Conflicts
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
