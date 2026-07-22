import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter/foundation.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Arıza Teşhis Asistanı',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey),
        useMaterial3: true,
      ),
      home: const ChatScreen(),
      debugShowCheckedModeBanner: false,
      home: DiagnosticChatScreen(),
    );
  }
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  
  // Artık sadece String değil, tüm JSON yanıtını tutacağız
  Map<String, dynamic>? _diagnosticResponse;
  String? _errorMessage;
  bool _isLoading = false;

  String getApiUrl() {
    if (kIsWeb) {
      return 'http://127.0.0.1:8000/api/diagnostics/query';
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/diagnostics/query';
    } else {
      return 'http://127.0.0.1:8000/api/diagnostics/query';
    }
  }

  Future<void> sendQuery() async {
    if (_controller.text.length < 5) {
      setState(() {
        _errorMessage = 'Lütfen en az 5 karakterlik bir arıza belirtisi girin.';
        _diagnosticResponse = null;
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _diagnosticResponse = null;
    });

    try {
      final url = Uri.parse(getApiUrl());
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'question': _controller.text}),
      );

      if (response.statusCode == 200) {
        final decodedBody = utf8.decode(response.bodyBytes);
        final data = json.decode(decodedBody);
        
        setState(() {
          // Tüm yanıtı state'e kaydediyoruz
          _diagnosticResponse = data;
        });
      } else {
        setState(() {
          _errorMessage = 'Hata: Sunucu ${response.statusCode} döndürdü.';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Bağlantı hatası: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  // Güven skoruna göre renk belirleyen yardımcı fonksiyon
  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.8) return Colors.green;
    if (confidence >= 0.5) return Colors.orange;
    return Colors.red;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Arıza Teşhis Asistanı'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Expanded(
              child: _buildResponseArea(),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: 'Arıza belirtilerini yazın...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => sendQuery(),
                  ),
                ),
                const SizedBox(width: 8),
                _isLoading
                    ? const CircularProgressIndicator()
                    : IconButton(
                        icon: const Icon(Icons.send),
                        color: Colors.blueGrey,
                        onPressed: sendQuery,
                      ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // Yanıt ekranını dinamik olarak oluşturan widget
  Widget _buildResponseArea() {
    if (_isLoading) {
      return const Center(child: Text('Teşhis yapılıyor, lütfen bekleyin...'));
    }

    if (_errorMessage != null) {
      return Center(
        child: Text(
          _errorMessage!,
          style: const TextStyle(color: Colors.red, fontSize: 16),
        ),
      );
    }

    if (_diagnosticResponse == null) {
      return const Center(child: Text('Asistana bir soru sorun...'));
    }

    // JSON'dan verileri çekiyoruz
    final answer = _diagnosticResponse!['answer'] ?? '';
    final confidence = (_diagnosticResponse!['confidence'] ?? 0.0) as double;
    final sources = _diagnosticResponse!['sources'] as List<dynamic>? ?? [];
    final warning = _diagnosticResponse!['warning'];

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Ana Cevap Kartı
          Card(
            elevation: 3,
            margin: const EdgeInsets.only(bottom: 16),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.check_circle, color: Colors.blueGrey),
                      const SizedBox(width: 8),
                      Text(
                        'Teşhis Sonucu',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                    ],
                  ),
                  const Divider(),
                  Text(
                    answer,
                    style: const TextStyle(fontSize: 16, height: 1.5),
                  ),
                ],
              ),
            ),
          ),

          // 2. Uyarı Mesajı (Eğer varsa)
          if (warning != null)
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: Colors.orange.shade100,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.orange.shade300),
              ),
              child: Row(
                children: [
                  const Icon(Icons.warning_amber_rounded, color: Colors.deepOrange),
                  const SizedBox(width: 8),
                  Expanded(child: Text(warning, style: const TextStyle(fontWeight: FontWeight.bold))),
                ],
              ),
            ),

          // 3. Güven Skoru Göstergesi
          Text(
            'Yapay Zeka Güven Skoru: ${(confidence * 100).toStringAsFixed(1)}%',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: confidence,
            backgroundColor: Colors.grey.shade300,
            color: _getConfidenceColor(confidence),
            minHeight: 10,
          ),
          const SizedBox(height: 24),

          // 4. Kaynak Dokümanlar
          if (sources.isNotEmpty) ...[
            const Text(
              'Referans Alınan Kaynaklar:',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 8),
            ...sources.map((source) {
              return Card(
                color: Colors.grey.shade50,
                child: ExpansionTile(
                  leading: const Icon(Icons.menu_book, color: Colors.blueGrey),
                  title: Text(
                    '${source['document_name']} (Sayfa: ${source['page_number']})',
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                  ),
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Text(
                        source['chunk_text'] ?? '',
                        style: const TextStyle(fontStyle: FontStyle.italic, color: Colors.black87),
                      ),
                    ),
                  ],
                ),
              );
            }),
          ]
        ],
      ),
    );
  }
}