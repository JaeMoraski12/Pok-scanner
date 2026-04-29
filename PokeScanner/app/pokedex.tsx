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
} from 'react-native';
import { CameraView, useCameraPermissions, CameraType } from 'expo-camera';
import { router } from 'expo-router';


// --- Styles ---
const styles = StyleSheet.create({
});