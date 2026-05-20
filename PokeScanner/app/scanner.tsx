import React from "react";
import { useState, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Image,
  Modal,
  Platform,
} from "react-native";
import { CameraView, useCameraPermissions, CameraType } from "expo-camera";
import { router } from "expo-router";

export default function ScannerScreen() {
  const [facing, setFacing] = useState<CameraType>("back");
  const [permission, requestPermission] = useCameraPermissions();
  const [isTakingPhoto, setIsTakingPhoto] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false); // New: for AI processing
  const cameraRef = useRef<CameraView>(null);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  // Get API URLs based on platform
  const getApiUrl = () => {
    const COMPUTER_IP = "100.66.101.40"; // Your computer's IP
    if (Platform.OS === "web") return "http://localhost:5000";
    if (Platform.OS === "ios" && !Platform.isPad)
      return "http://localhost:5000";
    if (Platform.OS === "android") return `http://${COMPUTER_IP}:5000`;
    return `http://${COMPUTER_IP}:5000`;
  };

  const getAiApiUrl = () => {
    const COMPUTER_IP = "100.66.101.40"; // Your computer's IP
    if (Platform.OS === "android") {
      return `http://${COMPUTER_IP}:8000`;
    }
    return "http://localhost:8000";
  };

  const API_BASE_URL = getApiUrl();
  const AI_API_URL = getAiApiUrl();

  if (!permission) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#e74c3c" />
        <Text style={styles.loadingText}>Loading camera...</Text>
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.messageText}>
          We need camera access to scan Pokémon
        </Text>
        <TouchableOpacity
          style={styles.permissionButton}
          onPress={requestPermission}
        >
          <Text style={styles.permissionButtonText}>Grant Permission</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // --- Camera Controls ---
  const toggleCameraFacing = () => {
    setFacing((current) => (current === "back" ? "front" : "back"));
  };

  const takePicture = async () => {
    if (cameraRef.current) {
      setIsTakingPhoto(true);
      try {
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.7,
          base64: true,
        });
        setCapturedPhoto(photo.uri);
        setShowPreview(true);
      } catch (error) {
        console.error("Error taking photo:", error);
        Alert.alert("Error", "Failed to take photo. Please try again.");
      } finally {
        setIsTakingPhoto(false);
      }
    }
  };

  const handleRetake = () => {
    setShowPreview(false);
    setCapturedPhoto(null);
  };

  // Send to AI and navigate to Pokédex
  const handleUsePhoto = async () => {
    if (!capturedPhoto) return;

    setShowPreview(false);
    setIsProcessing(true);

    try {
      // Show loading indicator
      Alert.alert("Processing", "Identifying Pokémon...", [{ text: "Wait" }], {
        cancelable: false,
      });

      // Convert image to base64
      const response = await fetch(capturedPhoto);
      const blob = await response.blob();
      const base64 = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          const result = reader.result as string;
          // Remove data:image/jpeg;base64, prefix
          const base64Data = result.split(",")[1];
          resolve(base64Data);
        };
        reader.readAsDataURL(blob);
      });

      // Step 1: Send to AI for prediction
      const aiResponse = await fetch(`${AI_API_URL}/api/predict-base64`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          image: base64,
          filename: "pokemon.jpg",
        }),
      });

      if (!aiResponse.ok) {
        throw new Error("AI prediction failed");
      }

      const aiResult = await aiResponse.json();
      const predictedPokemonName = aiResult.Prediction.toLowerCase();
      console.log("AI Predicted:", predictedPokemonName);

      // Step 2: Fetch Pokémon data from database
      const pokemonResponse = await fetch(
        `${API_BASE_URL}/api/pokemon/by-name/${predictedPokemonName}`,
      );

      if (!pokemonResponse.ok) {
        throw new Error(
          `Pokémon "${predictedPokemonName}" not found in database`,
        );
      }

      const pokemonData = await pokemonResponse.json();
      console.log("Pokemon data:", pokemonData);

      // Step 3: Navigate to Pokédex with the Pokémon data
      router.push({
        pathname: "/pokedex",
        params: {
          selectedPokemon: JSON.stringify(pokemonData),
          autoOpenModal: "true",
        },
      });

      // Clear the captured photo
      setCapturedPhoto(null);
    } catch (error) {
      console.error("Error processing photo:", error);
      Alert.alert(
        "Identification Failed",
        "Could not identify this Pokémon. Please try again with a clearer photo.",
        [{ text: "OK", onPress: () => setCapturedPhoto(null) }],
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const PreviewModal = () => (
    <Modal
      visible={showPreview}
      animationType="slide"
      transparent={false}
      onRequestClose={handleRetake}
    >
      <View style={styles.modalContainer}>
        <Text style={styles.modalTitle}>Your Photo</Text>
        {capturedPhoto && (
          <Image source={{ uri: capturedPhoto }} style={styles.previewImage} />
        )}

        <Text style={styles.questionText}>Do you want to use this photo?</Text>
        <View style={styles.modalButtons}>
          <TouchableOpacity
            style={[styles.modalButton, styles.retakeButton]}
            onPress={handleRetake}
          >
            <Text style={styles.buttonText}>Retake Photo</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modalButton, styles.useButton]}
            onPress={handleUsePhoto}
            disabled={isProcessing}
          >
            {isProcessing ? (
              <ActivityIndicator color="white" size="small" />
            ) : (
              <Text style={styles.buttonText}>Use This Photo</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  // --- Main Screen UI ---
  return (
    <>
      <View style={styles.container}>
        <CameraView
          ref={cameraRef}
          style={styles.camera}
          facing={facing}
          mode="picture"
        >
          <View style={styles.overlay}>
            <Text style={styles.scanText}>Center Pokémon in frame</Text>
            <TouchableOpacity
              style={styles.captureButton}
              onPress={takePicture}
              disabled={isTakingPhoto}
            >
              {isTakingPhoto ? (
                <ActivityIndicator color="white" />
              ) : (
                <View style={styles.captureButtonInner} />
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.flipButton}
              onPress={toggleCameraFacing}
            >
              <Text style={styles.flipButtonText}>⟳</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => router.back()}
            >
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
        </CameraView>
      </View>

      <PreviewModal />

      {/* Processing Modal */}
      <Modal visible={isProcessing} transparent={true} animationType="fade">
        <View style={styles.processingContainer}>
          <View style={styles.processingBox}>
            <ActivityIndicator size="large" color="#e74c3c" />
            <Text style={styles.processingText}>Identifying Pokémon...</Text>
            <Text style={styles.processingSubtext}>This may take a moment</Text>
          </View>
        </View>
      </Modal>
    </>
  );
}

// --- Styles ---
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "black",
  },
  camera: {
    flex: 1,
  },
  overlay: {
    flex: 1,
    backgroundColor: "transparent",
    justifyContent: "space-between",
    paddingVertical: 50,
  },
  scanText: {
    textAlign: "center",
    color: "white",
    fontSize: 18,
    fontWeight: "600",
    backgroundColor: "rgba(0,0,0,0.6)",
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignSelf: "center",
    borderRadius: 20,
    marginTop: 20,
  },
  captureButton: {
    alignSelf: "center",
    backgroundColor: "rgba(255,255,255,0.3)",
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 30,
  },
  captureButtonInner: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: "white",
    borderWidth: 2,
    borderColor: "#e74c3c",
  },
  flipButton: {
    position: "absolute",
    top: 60,
    right: 20,
    backgroundColor: "rgba(0,0,0,0.6)",
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: "center",
    alignItems: "center",
  },
  flipButtonText: {
    color: "white",
    fontSize: 28,
    fontWeight: "bold",
  },
  closeButton: {
    position: "absolute",
    top: 60,
    left: 20,
    backgroundColor: "rgba(0,0,0,0.6)",
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: "center",
    alignItems: "center",
  },
  closeButtonText: {
    color: "white",
    fontSize: 24,
    fontWeight: "bold",
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f5f5f5",
    padding: 20,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: "#666",
  },
  messageText: {
    fontSize: 18,
    textAlign: "center",
    marginBottom: 20,
    color: "#333",
  },
  permissionButton: {
    backgroundColor: "#e74c3c",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10,
    marginBottom: 15,
  },
  permissionButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  backButton: {
    backgroundColor: "#3498db",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10,
  },
  backButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  modalContainer: {
    flex: 1,
    backgroundColor: "#f5f5f5",
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  modalTitle: {
    fontSize: 28,
    fontWeight: "bold",
    color: "#2c3e50",
    marginBottom: 20,
  },
  previewImage: {
    width: 300,
    height: 300,
    borderRadius: 20,
    marginBottom: 30,
    borderWidth: 3,
    borderColor: "#e74c3c",
  },
  questionText: {
    fontSize: 22,
    fontWeight: "600",
    color: "#2c3e50",
    marginBottom: 30,
    textAlign: "center",
  },
  modalButtons: {
    flexDirection: "row",
    gap: 15,
    justifyContent: "center",
  },
  modalButton: {
    paddingVertical: 15,
    paddingHorizontal: 25,
    borderRadius: 10,
    alignItems: "center",
    minWidth: 140,
  },
  retakeButton: {
    backgroundColor: "#f39c12",
  },
  useButton: {
    backgroundColor: "#2ecc71",
  },
  buttonText: {
    color: "white",
    fontSize: 18,
    fontWeight: "600",
  },
  processingContainer: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.8)",
    justifyContent: "center",
    alignItems: "center",
  },
  processingBox: {
    backgroundColor: "white",
    padding: 30,
    borderRadius: 20,
    alignItems: "center",
    gap: 15,
    minWidth: 250,
  },
  processingText: {
    fontSize: 20,
    fontWeight: "600",
    color: "#2c3e50",
  },
  processingSubtext: {
    fontSize: 14,
    color: "#999",
  },
});
