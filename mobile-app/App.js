import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, Alert } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

const Stack = createStackNavigator();
const API_URL = 'http://your-server-url/api/mobile';

const LoginScreen = ({ navigation }) => {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone, password }),
      });
      const data = await response.json();
      if (response.ok) {
        navigation.navigate('Home', { user: data.user });
      } else {
        Alert.alert('Lỗi', 'Đăng nhập thất bại');
      }
    } catch (error) {
      Alert.alert('Lỗi', 'Không thể kết nối đến máy chủ');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Phòng khám Phụ Sản Đại Anh</Text>
      <TextInput
        style={styles.input}
        placeholder="Số điện thoại"
        value={phone}
        onChangeText={setPhone}
        keyboardType="phone-pad"
      />
      <TextInput
        style={styles.input}
        placeholder="Mật khẩu"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <TouchableOpacity style={styles.button} onPress={handleLogin}>
        <Text style={styles.buttonText}>Đăng nhập</Text>
      </TouchableOpacity>
    </View>
  );
};

const HomeScreen = ({ route }) => {
  const { user } = route.params;
  const [appointments, setAppointments] = useState([]);
  const [medicalRecords, setMedicalRecords] = useState([]);

  useEffect(() => {
    loadAppointments();
    loadMedicalRecords();
  }, []);

  const loadAppointments = async () => {
    try {
      const response = await fetch(`${API_URL}/appointments?patient_id=${user.id}`);
      const data = await response.json();
      setAppointments(data);
    } catch (error) {
      Alert.alert('Lỗi', 'Không thể tải lịch hẹn');
    }
  };

  const loadMedicalRecords = async () => {
    try {
      const response = await fetch(`${API_URL}/medical-records?patient_id=${user.id}`);
      const data = await response.json();
      setMedicalRecords(data);
    } catch (error) {
      Alert.alert('Lỗi', 'Không thể tải hồ sơ bệnh án');
    }
  };

  const renderAppointment = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>Lịch hẹn ngày {new Date(item.date).toLocaleDateString('vi-VN')}</Text>
      <Text>Dịch vụ: {item.service_type}</Text>
      <Text>Trạng thái: {item.status}</Text>
    </View>
  );

  const renderMedicalRecord = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>Ngày khám: {new Date(item.date).toLocaleDateString('vi-VN')}</Text>
      <Text>Chẩn đoán: {item.diagnosis}</Text>
      <Text>Đơn thuốc: {item.prescription}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.welcome}>Xin chào, {user.name}</Text>
      
      <Text style={styles.sectionTitle}>Lịch hẹn sắp tới</Text>
      <FlatList
        data={appointments}
        renderItem={renderAppointment}
        keyExtractor={item => item.id.toString()}
      />

      <Text style={styles.sectionTitle}>Hồ sơ bệnh án</Text>
      <FlatList
        data={medicalRecords}
        renderItem={renderMedicalRecord}
        keyExtractor={item => item.id.toString()}
      />
    </View>
  );
};

const App = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
        <Stack.Screen name="Home" component={HomeScreen} options={{ headerShown: false }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  input: {
    height: 40,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 5,
    marginBottom: 10,
    paddingHorizontal: 10,
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 5,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  welcome: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 20,
    marginBottom: 10,
  },
  card: {
    backgroundColor: '#f8f8f8',
    padding: 15,
    borderRadius: 5,
    marginBottom: 10,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
});

export default App; 