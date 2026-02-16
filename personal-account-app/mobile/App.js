import React, { useEffect, useMemo, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import {
  Alert,
  FlatList,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = 'ledgerEntries';

const formatAmount = (value) => value.toFixed(2);

export default function App() {
  const [entries, setEntries] = useState([]);
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const loadEntries = async () => {
      try {
        const stored = await AsyncStorage.getItem(STORAGE_KEY);
        if (stored) {
          setEntries(JSON.parse(stored));
        }
      } catch (error) {
        Alert.alert('提示', '读取本地数据失败，请稍后重试。');
      } finally {
        setReady(true);
      }
    };

    loadEntries();
  }, []);

  useEffect(() => {
    if (!ready) {
      return;
    }

    AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(entries)).catch(() => {
      Alert.alert('提示', '保存本地数据失败，请稍后重试。');
    });
  }, [entries, ready]);

  const balance = useMemo(
    () => entries.reduce((sum, entry) => sum + entry.amount, 0),
    [entries]
  );

  const handleAdd = (type) => {
    const parsed = Number(amount);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      Alert.alert('提示', '请输入正确金额。');
      return;
    }

    const entryAmount = type === 'saving' ? parsed : -parsed;
    const newEntry = {
      id: `${Date.now()}`,
      type,
      amount: entryAmount,
      note: note.trim(),
      date: new Date().toISOString().slice(0, 10),
    };

    setEntries([newEntry, ...entries]);
    setAmount('');
    setNote('');
  };

  const renderEntry = ({ item }) => (
    <View style={styles.entryRow}>
      <Text style={styles.entryType}>{item.type === 'saving' ? '存钱' : '记账'}</Text>
      <View style={styles.entryInfo}>
        <Text style={styles.entryNote}>{item.note || '（无备注）'}</Text>
        <Text style={styles.entryDate}>{item.date}</Text>
      </View>
      <Text
        style={[
          styles.entryAmount,
          item.amount >= 0 ? styles.amountPositive : styles.amountNegative,
        ]}
      >
        {item.amount >= 0 ? '+' : '-'}￥{formatAmount(Math.abs(item.amount))}
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      <Text style={styles.title}>个人账本</Text>
      <View style={styles.balanceCard}>
        <Text style={styles.balanceLabel}>当前余额</Text>
        <Text style={styles.balanceAmount}>￥{formatAmount(balance)}</Text>
        <Text style={styles.balanceHint}>纯本地保存 · 无需联网</Text>
      </View>
      <View style={styles.form}>
        <TextInput
          style={styles.input}
          placeholder="金额（元）"
          keyboardType="decimal-pad"
          value={amount}
          onChangeText={setAmount}
        />
        <TextInput
          style={styles.input}
          placeholder="备注（可不填）"
          value={note}
          onChangeText={setNote}
        />
        <View style={styles.actions}>
          <Pressable
            style={({ pressed }) => [
              styles.button,
              styles.buttonPrimary,
              pressed && styles.buttonPressed,
            ]}
            onPress={() => handleAdd('saving')}
          >
            <Text style={styles.buttonText}>存钱</Text>
          </Pressable>
          <Pressable
            style={({ pressed }) => [
              styles.button,
              styles.buttonSecondary,
              pressed && styles.buttonPressed,
            ]}
            onPress={() => handleAdd('expense')}
          >
            <Text style={styles.buttonText}>记账</Text>
          </Pressable>
        </View>
      </View>
      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        renderItem={renderEntry}
        contentContainerStyle={[
          styles.list,
          entries.length === 0 && styles.listEmpty,
        ]}
        ListEmptyComponent={
          <Text style={styles.emptyText}>暂无记录，先存一笔吧。</Text>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f7f7f5',
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1c1c1c',
    textAlign: 'center',
    marginTop: 12,
  },
  balanceCard: {
    backgroundColor: '#ffffff',
    borderRadius: 18,
    padding: 20,
    marginTop: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  balanceLabel: {
    fontSize: 16,
    color: '#666',
  },
  balanceAmount: {
    fontSize: 34,
    fontWeight: '700',
    color: '#0b7a4d',
    marginTop: 6,
  },
  balanceHint: {
    marginTop: 6,
    color: '#888',
    fontSize: 14,
  },
  form: {
    marginTop: 18,
    backgroundColor: '#ffffff',
    borderRadius: 18,
    padding: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 14,
    fontSize: 18,
    marginBottom: 12,
    backgroundColor: '#fafafa',
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  button: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonPrimary: {
    backgroundColor: '#0b7a4d',
    marginRight: 8,
  },
  buttonSecondary: {
    backgroundColor: '#375a9e',
    marginLeft: 8,
  },
  buttonPressed: {
    opacity: 0.85,
  },
  buttonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '600',
  },
  list: {
    paddingVertical: 16,
  },
  listEmpty: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    color: '#888',
  },
  entryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
  },
  entryType: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    width: 56,
  },
  entryInfo: {
    flex: 1,
    marginLeft: 8,
  },
  entryNote: {
    fontSize: 18,
    color: '#222',
  },
  entryDate: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  entryAmount: {
    fontSize: 20,
    fontWeight: '700',
  },
  amountPositive: {
    color: '#0b7a4d',
  },
  amountNegative: {
    color: '#c0392b',
  },
});
