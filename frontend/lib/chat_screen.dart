import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'app_config.dart';

class DiagnosticChatScreen extends StatefulWidget {
  const DiagnosticChatScreen({super.key});

  @override
  State<DiagnosticChatScreen> createState() => _DiagnosticChatScreenState();
}

class _DiagnosticChatScreenState extends State<DiagnosticChatScreen> {
  static const Color _pageBackground = Color(0xFF09111F);
  static const Color _panelBorder = Color(0xFF1B2940);
  static const Color _accent = Color(0xFF4DA2FF);

  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  final List<ChatMessage> _messages = <ChatMessage>[
    const ChatMessage.assistant(
      text:
          'Merhaba. Ben Rayli Sistemler Ariza Teshis Asistaniyim. Teknik belirtiyi veya bakim sorunu yaz, ben de yerel dokumanlara gore cevaplayayim.',
    ),
  ];

  String? _sessionId;
  bool _isLoading = false;
  String? _statusText;

  Future<void> _sendMessage() async {
    final String question = _messageController.text.trim();
    if (question.isEmpty) {
      return;
    }

    if (question.length < 5) {
      setState(() {
        _statusText = 'Lutfen en az 5 karakterlik bir soru gir.';
      });
      return;
    }

    setState(() {
      _messages.add(ChatMessage.user(text: question));
      _messageController.clear();
      _isLoading = true;
      _statusText = null;
    });
    _scrollToBottom();

    try {
      final http.Response response = await http.post(
        Uri.parse('${AppConfig.apiBaseUrl()}/diagnostics/query'),
        headers: <String, String>{'Content-Type': 'application/json'},
        body: jsonEncode(<String, dynamic>{
          'question': question,
          'session_id': _sessionId,
          'top_k': 3,
        }),
      );

      if (response.statusCode != 200) {
        setState(() {
          _messages.add(
            ChatMessage.system(
              text:
                  'Sunucu beklenen cevabi donmedi. Durum kodu: ${response.statusCode}',
            ),
          );
        });
        return;
      }

      final Map<String, dynamic> data =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;

      setState(() {
        _sessionId = data['session_id']?.toString();
        _messages.add(
          ChatMessage.assistant(
            text: data['answer']?.toString() ?? 'Bos cevap alindi.',
            warning: data['warning']?.toString(),
            grounded: data['grounded'] as bool? ?? false,
            confidence: (data['confidence'] as num?)?.toDouble(),
          ),
        );
      });
    } catch (error) {
      setState(() {
        _messages.add(
          ChatMessage.system(
            text: '${AppConfig.backendHelpText()} Detay: $error',
          ),
        );
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _pageBackground,
      appBar: AppBar(
        elevation: 0,
        titleSpacing: 0,
        toolbarHeight: 82,
        title: const Padding(
          padding: EdgeInsets.only(left: 4),
          child: _AppHeader(),
        ),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 10),
            child: TextButton.icon(
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (BuildContext context) => const TestLabScreen(),
                  ),
                );
              },
              icon: const Icon(Icons.science_outlined, size: 18),
              label: const Text('Test Lab'),
            ),
          ),
        ],
        flexibleSpace: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: <Color>[Color(0xFF132238), Color(0xFF0A1220)],
            ),
            border: Border(
              bottom: BorderSide(color: _panelBorder),
            ),
          ),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: <Widget>[
            Expanded(
              child: RefreshIndicator(
                onRefresh: () async {},
                color: _accent,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(14, 16, 14, 12),
                  children: <Widget>[
                    Container(
                      height: 360,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: <Color>[
                            Color(0xFF0F1B2D),
                            Color(0xFF0B1525),
                          ],
                        ),
                        borderRadius: BorderRadius.circular(28),
                        border: Border.all(color: _panelBorder),
                        boxShadow: const <BoxShadow>[
                          BoxShadow(
                            color: Color(0x40000000),
                            blurRadius: 28,
                            offset: Offset(0, 14),
                          ),
                        ],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(28),
                        child: ListView.builder(
                          controller: _scrollController,
                          padding: const EdgeInsets.fromLTRB(16, 18, 16, 12),
                          itemCount: _messages.length,
                          itemBuilder: (BuildContext context, int index) {
                            return _MessageSection(message: _messages[index]);
                          },
                        ),
                      ),
                    ),
                    if (_isLoading)
                      const Padding(
                        padding: EdgeInsets.fromLTRB(8, 12, 8, 0),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: _TypingIndicator(),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            if (_statusText != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    _statusText!,
                    style: const TextStyle(
                      color: Color(0xFFFF8B8B),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            _Composer(
              controller: _messageController,
              isLoading: _isLoading,
              onSend: _sendMessage,
            ),
          ],
        ),
      ),
    );
  }
}

class TestLabScreen extends StatefulWidget {
  const TestLabScreen({super.key});

  @override
  State<TestLabScreen> createState() => _TestLabScreenState();
}

class _TestLabScreenState extends State<TestLabScreen> {
  static const Color _pageBackground = Color(0xFF09111F);
  static const Color _panelBorder = Color(0xFF1B2940);
  static const Color _accent = Color(0xFF4DA2FF);

  final TextEditingController _testQuestionController = TextEditingController();
  final TextEditingController _testKeywordsController = TextEditingController();

  List<TestCaseItem> _testCases = <TestCaseItem>[];
  TestRunResult? _lastTestRun;
  String _expectedBehavior = 'answerable';
  bool _isCreatingTest = false;
  int? _runningTestId;
  String? _statusText;

  @override
  void initState() {
    super.initState();
    _fetchTestCases();
  }

  Future<void> _fetchTestCases() async {
    try {
      final http.Response response = await http.get(
        Uri.parse('${AppConfig.apiBaseUrl()}/tests/cases'),
      );
      if (response.statusCode != 200) {
        throw Exception('Durum kodu: ${response.statusCode}');
      }

      final List<dynamic> data =
          jsonDecode(utf8.decode(response.bodyBytes)) as List<dynamic>;
      setState(() {
        _testCases = data
            .map(
              (dynamic item) =>
                  TestCaseItem.fromJson(item as Map<String, dynamic>),
            )
            .toList();
      });
    } catch (error) {
      setState(() {
        _statusText = '${AppConfig.backendHelpText()} Detay: $error';
      });
    }
  }

  Future<void> _createTestCase() async {
    final String question = _testQuestionController.text.trim();
    final String keywords = _testKeywordsController.text.trim();

    if (question.length < 5) {
      setState(() {
        _statusText = 'Test sorusu en az 5 karakter olmali.';
      });
      return;
    }

    setState(() {
      _isCreatingTest = true;
      _statusText = null;
    });

    try {
      final http.Response response = await http.post(
        Uri.parse('${AppConfig.apiBaseUrl()}/tests/cases'),
        headers: <String, String>{'Content-Type': 'application/json'},
        body: jsonEncode(<String, dynamic>{
          'question': question,
          'expected_behavior': _expectedBehavior,
          'expected_keywords': keywords.isEmpty ? null : keywords,
        }),
      );

      if (response.statusCode != 200) {
        throw Exception('Durum kodu: ${response.statusCode}');
      }

      _testQuestionController.clear();
      _testKeywordsController.clear();
      await _fetchTestCases();

      setState(() {
        _statusText = 'Test case eklendi.';
      });
    } catch (error) {
      setState(() {
        _statusText = '${AppConfig.backendHelpText()} Detay: $error';
      });
    } finally {
      setState(() {
        _isCreatingTest = false;
      });
    }
  }

  Future<void> _runTestCase(TestCaseItem item) async {
    setState(() {
      _runningTestId = item.id;
      _statusText = null;
    });

    try {
      final http.Response response = await http.post(
        Uri.parse('${AppConfig.apiBaseUrl()}/tests/cases/${item.id}/run'),
        headers: <String, String>{'Content-Type': 'application/json'},
        body: jsonEncode(<String, dynamic>{'top_k': 3}),
      );

      if (response.statusCode != 200) {
        throw Exception('Durum kodu: ${response.statusCode}');
      }

      final Map<String, dynamic> data =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      setState(() {
        _lastTestRun = TestRunResult.fromJson(data);
        _statusText = data['notes']?.toString();
      });
    } catch (error) {
      setState(() {
        _statusText = '${AppConfig.backendHelpText()} Detay: $error';
      });
    } finally {
      setState(() {
        _runningTestId = null;
      });
    }
  }

  @override
  void dispose() {
    _testQuestionController.dispose();
    _testKeywordsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _pageBackground,
      appBar: AppBar(
        title: const Text('Test Laboratuvari'),
        flexibleSpace: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: <Color>[Color(0xFF132238), Color(0xFF0A1220)],
            ),
            border: Border(
              bottom: BorderSide(color: _panelBorder),
            ),
          ),
        ),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _fetchTestCases,
          color: _accent,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(14, 16, 14, 16),
            children: <Widget>[
              _TestLabCard(
                testQuestionController: _testQuestionController,
                testKeywordsController: _testKeywordsController,
                expectedBehavior: _expectedBehavior,
                isCreatingTest: _isCreatingTest,
                runningTestId: _runningTestId,
                testCases: _testCases,
                lastTestRun: _lastTestRun,
                onBehaviorChanged: (String? value) {
                  if (value == null) {
                    return;
                  }
                  setState(() {
                    _expectedBehavior = value;
                  });
                },
                onCreateTest: _createTestCase,
                onRunTest: _runTestCase,
              ),
              if (_statusText != null) ...<Widget>[
                const SizedBox(height: 12),
                Text(
                  _statusText!,
                  style: const TextStyle(
                    color: Color(0xFFFF8B8B),
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class ChatMessage {
  const ChatMessage({
    required this.text,
    required this.role,
    this.warning,
    this.grounded,
    this.confidence,
  });

  const ChatMessage.user({required String text})
      : this(text: text, role: MessageRole.user);

  const ChatMessage.assistant({
    required String text,
    String? warning,
    bool? grounded,
    double? confidence,
  }) : this(
          text: text,
          role: MessageRole.assistant,
          warning: warning,
          grounded: grounded,
          confidence: confidence,
        );

  const ChatMessage.system({required String text})
      : this(text: text, role: MessageRole.system);

  final String text;
  final MessageRole role;
  final String? warning;
  final bool? grounded;
  final double? confidence;
}

class TestCaseItem {
  const TestCaseItem({
    required this.id,
    required this.question,
    required this.expectedBehavior,
    this.expectedKeywords,
  });

  factory TestCaseItem.fromJson(Map<String, dynamic> json) {
    return TestCaseItem(
      id: (json['id'] as num? ?? 0).toInt(),
      question: json['question']?.toString() ?? '',
      expectedBehavior: json['expected_behavior']?.toString() ?? 'answerable',
      expectedKeywords: json['expected_keywords']?.toString(),
    );
  }

  final int id;
  final String question;
  final String expectedBehavior;
  final String? expectedKeywords;
}

class TestRunResult {
  const TestRunResult({
    required this.testCaseId,
    required this.passed,
    required this.notes,
    required this.answer,
  });

  factory TestRunResult.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> response =
        json['response'] as Map<String, dynamic>? ?? <String, dynamic>{};
    return TestRunResult(
      testCaseId: (json['test_case_id'] as num? ?? 0).toInt(),
      passed: json['passed'] as bool? ?? false,
      notes: json['notes']?.toString() ?? '',
      answer: response['answer']?.toString() ?? '',
    );
  }

  final int testCaseId;
  final bool passed;
  final String notes;
  final String answer;
}

enum MessageRole { user, assistant, system }

class _AppHeader extends StatelessWidget {
  const _AppHeader();

  @override
  Widget build(BuildContext context) {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        Text(
          'Rayli Sistemler Asistani',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.2,
          ),
        ),
        SizedBox(height: 2),
        Text(
          'Yerel RAG destekli teshis paneli',
          style: TextStyle(fontSize: 12, color: Color(0xFF8EA4C1)),
        ),
      ],
    );
  }
}

class _TestLabCard extends StatelessWidget {
  const _TestLabCard({
    required this.testQuestionController,
    required this.testKeywordsController,
    required this.expectedBehavior,
    required this.isCreatingTest,
    required this.runningTestId,
    required this.testCases,
    required this.lastTestRun,
    required this.onBehaviorChanged,
    required this.onCreateTest,
    required this.onRunTest,
  });

  final TextEditingController testQuestionController;
  final TextEditingController testKeywordsController;
  final String expectedBehavior;
  final bool isCreatingTest;
  final int? runningTestId;
  final List<TestCaseItem> testCases;
  final TestRunResult? lastTestRun;
  final ValueChanged<String?> onBehaviorChanged;
  final VoidCallback onCreateTest;
  final ValueChanged<TestCaseItem> onRunTest;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF0F1B2D),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFF1B2940)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text(
            'Test Laboratuvari',
            style: TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 14),
          TextField(
            controller: testQuestionController,
            style: const TextStyle(color: Colors.white),
            decoration: const InputDecoration(
              hintText: 'Test sorusu yaz...',
              hintStyle: TextStyle(color: Color(0xFF6F819A)),
            ),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: testKeywordsController,
            style: const TextStyle(color: Colors.white),
            decoration: const InputDecoration(
              hintText: 'Beklenen anahtar kelimeler (virgulle)',
              hintStyle: TextStyle(color: Color(0xFF6F819A)),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: <Widget>[
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: expectedBehavior,
                  dropdownColor: const Color(0xFF121F33),
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(
                    labelText: 'Beklenen davranis',
                    labelStyle: TextStyle(color: Color(0xFF8EA4C1)),
                  ),
                  items: const <DropdownMenuItem<String>>[
                    DropdownMenuItem<String>(
                      value: 'answerable',
                      child: Text('Answerable'),
                    ),
                    DropdownMenuItem<String>(
                      value: 'unanswerable',
                      child: Text('Unanswerable'),
                    ),
                  ],
                  onChanged: onBehaviorChanged,
                ),
              ),
              const SizedBox(width: 10),
              FilledButton(
                onPressed: isCreatingTest ? null : onCreateTest,
                style: FilledButton.styleFrom(
                  backgroundColor: const Color(0xFF4DA2FF),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 18,
                    vertical: 18,
                  ),
                ),
                child: Text(isCreatingTest ? 'Ekleniyor' : 'Test Ekle'),
              ),
            ],
          ),
          const SizedBox(height: 18),
          const Text(
            'Kayitli Testler',
            style: TextStyle(
              color: Color(0xFFE5EDF8),
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 10),
          if (testCases.isEmpty)
            const Text(
              'Henuz test case yok.',
              style: TextStyle(color: Color(0xFFAAB6CA)),
            )
          else
            ...testCases.map(
              (TestCaseItem item) => Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFF121F33),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: const Color(0xFF22334A)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            item.question,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Beklenen: ${item.expectedBehavior}'
                            '${item.expectedKeywords == null ? '' : ' | Anahtar: ${item.expectedKeywords}'}',
                            style: const TextStyle(
                              color: Color(0xFF8EA4C1),
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 10),
                    OutlinedButton(
                      onPressed:
                          runningTestId == item.id ? null : () => onRunTest(item),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.white,
                        side: const BorderSide(color: Color(0xFF4DA2FF)),
                      ),
                      child: Text(
                        runningTestId == item.id ? 'Calisiyor' : 'Calistir',
                      ),
                    ),
                  ],
                ),
              ),
            ),
          if (lastTestRun != null) ...<Widget>[
            const SizedBox(height: 14),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: lastTestRun!.passed
                    ? const Color(0xFF0D2B1B)
                    : const Color(0xFF34181A),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: lastTestRun!.passed
                      ? const Color(0xFF1C7C54)
                      : const Color(0xFF8E2F39),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    lastTestRun!.passed
                        ? 'Son test basarili'
                        : 'Son test basarisiz',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    lastTestRun!.notes,
                    style: const TextStyle(color: Color(0xFFE5EDF8)),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    lastTestRun!.answer,
                    style: const TextStyle(color: Color(0xFFAAB6CA)),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _MessageSection extends StatelessWidget {
  const _MessageSection({required this.message});

  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final bool isUser = message.role == MessageRole.user;
    final bool isSystem = message.role == MessageRole.system;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Padding(
        padding: const EdgeInsets.only(bottom: 14),
        child: ConstrainedBox(
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.82,
          ),
          child: Column(
            crossAxisAlignment:
                isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
            children: <Widget>[
              _MessageBubble(message: message, isSystem: isSystem),
              if (message.warning != null && message.warning!.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: _WarningCard(text: message.warning!),
                ),
              if (message.role == MessageRole.assistant &&
                  message.confidence != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: _ConfidenceCard(
                    confidence: message.confidence!,
                    grounded: message.grounded ?? false,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message, required this.isSystem});

  final ChatMessage message;
  final bool isSystem;

  @override
  Widget build(BuildContext context) {
    final bool isUser = message.role == MessageRole.user;
    final Color backgroundColor = isUser
        ? const Color(0xFF1E3A5F)
        : isSystem
            ? const Color(0xFF3A1820)
            : const Color(0xFF121F33);
    final Color textColor = isUser
        ? Colors.white
        : isSystem
            ? const Color(0xFFFFC4C4)
            : const Color(0xFFF5F7FA);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.only(
          topLeft: const Radius.circular(18),
          topRight: const Radius.circular(18),
          bottomLeft: Radius.circular(isUser ? 18 : 4),
          bottomRight: Radius.circular(isUser ? 4 : 18),
        ),
        border: Border.all(
          color: isUser ? const Color(0xFF3C5D87) : const Color(0xFF22334A),
        ),
      ),
      child: Text(
        message.text,
        style: TextStyle(
          color: textColor,
          fontSize: 14.5,
          height: 1.55,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}

class _WarningCard extends StatelessWidget {
  const _WarningCard({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF312611),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF8E6A2A)),
      ),
      child: Row(
        children: <Widget>[
          const Icon(
            Icons.warning_amber_rounded,
            color: Color(0xFFB54708),
            size: 18,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: Color(0xFFFFE2B8),
                fontSize: 12.5,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ConfidenceCard extends StatelessWidget {
  const _ConfidenceCard({
    required this.confidence,
    required this.grounded,
  });

  final double confidence;
  final bool grounded;

  Color _barColor() {
    if (confidence >= 0.8) {
      return const Color(0xFF079455);
    }
    if (confidence >= 0.5) {
      return const Color(0xFFDC6803);
    }
    return const Color(0xFFD92D20);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0C1727),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF22334A)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(
                grounded ? Icons.verified_outlined : Icons.help_outline,
                size: 16,
                color: grounded
                    ? const Color(0xFF4DA2FF)
                    : const Color(0xFFB54708),
              ),
              const SizedBox(width: 6),
              Text(
                grounded ? 'Grounded yanit' : 'Grounding zayif',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFFE5EDF8),
                ),
              ),
              const Spacer(),
              Text(
                '% ${(confidence * 100).toStringAsFixed(0)}',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFFE5EDF8),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              value: confidence,
              minHeight: 8,
              backgroundColor: const Color(0xFF243247),
              valueColor: AlwaysStoppedAnimation<Color>(_barColor()),
            ),
          ),
        ],
      ),
    );
  }
}

class _TypingIndicator extends StatelessWidget {
  const _TypingIndicator();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF121F33),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF22334A)),
      ),
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          SizedBox(
            width: 14,
            height: 14,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF4DA2FF)),
            ),
          ),
          SizedBox(width: 10),
          Text(
            'Dokumanlar taraniyor...',
            style: TextStyle(
              color: Color(0xFFAAB6CA),
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.isLoading,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool isLoading;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    const Color accent = Color(0xFF4DA2FF);

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
      decoration: const BoxDecoration(
        color: Color(0xFF0C1727),
        border: Border(
          top: BorderSide(color: Color(0xFF1B2940)),
        ),
      ),
      child: SafeArea(
        top: false,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: <Widget>[
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFF121F33),
                  borderRadius: BorderRadius.circular(22),
                  border: Border.all(color: const Color(0xFF243247)),
                ),
                child: TextField(
                  controller: controller,
                  minLines: 1,
                  maxLines: 5,
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) => isLoading ? null : onSend(),
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w500,
                  ),
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    hintText: 'Ariza belirtisini veya bakim sorusunu yaz...',
                    hintStyle: TextStyle(color: Color(0xFF6F819A)),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 10),
            Material(
              color: isLoading ? const Color(0xFF44566F) : accent,
              borderRadius: BorderRadius.circular(20),
              shadowColor: const Color(0x80234D7C),
              elevation: 8,
              child: InkWell(
                borderRadius: BorderRadius.circular(20),
                onTap: isLoading ? null : onSend,
                child: const SizedBox(
                  width: 52,
                  height: 52,
                  child: Icon(Icons.send_rounded, color: Colors.white),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
