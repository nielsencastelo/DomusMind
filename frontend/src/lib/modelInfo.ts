import { ProviderKey } from "@/lib/api";

export function yoloModelDescription(name: string): string {
  const key = name.toLowerCase();
  if (key.includes("yolov8n")) return "Nano: mais leve e rapido. Bom para CPU, testes e cameras simples; menor precisao.";
  if (key.includes("yolov8s")) return "Small: equilibrio leve. Bom para uso continuo com pouco consumo.";
  if (key.includes("yolov8m")) return "Medium: melhor precisao sem ficar tao pesado. Boa escolha geral se houver GPU.";
  if (key.includes("yolov8l")) return "Large: mais preciso, mais lento. Indicado quando detalhes importam.";
  if (key.includes("yolov8x")) return "Extra large: maior precisao da familia YOLOv8, mas exige mais CPU/GPU e memoria.";
  if (key.endsWith(".pt")) return "Modelo YOLO personalizado encontrado em models. Use se voce conhece o peso e as classes treinadas.";
  return "Modelo de visao local. Quanto maior o modelo, melhor tende a ser a precisao e maior o custo de processamento.";
}

export function llmModelDescription(provider: ProviderKey, id: string): string {
  const model = id.toLowerCase();

  if (provider === "local") {
    if (model.includes("nomic-embed")) return "Embedding local para memoria/RAG. Nao e modelo de conversa.";
    if (model.includes("phi")) return "Modelo local leve e rapido. Bom para classificacao, automacao e respostas curtas.";
    if (model.includes("llama") || model.includes("qwen") || model.includes("mistral")) return "Modelo local de conversa. Privado e sem custo por API, mas depende da sua maquina.";
    if (model.includes("vision") || model.includes("llava")) return "Modelo local multimodal. Pode analisar imagens se o fluxo suportar entrada visual.";
    return "Modelo instalado no Ollama local. Melhor para privacidade, testes offline e tarefas simples.";
  }

  if (provider === "gemini") {
    if (model.includes("flash")) return "Rapido e economico. Boa opcao para chat, classificacao, automacao e visao cotidiana.";
    if (model.includes("pro")) return "Mais forte para raciocinio e tarefas complexas, com maior latencia/custo.";
    if (model.includes("embedding")) return "Modelo de embedding do Google. Use para memoria/RAG, nao para chat.";
    return "Modelo Gemini online. Bom para multimodalidade, visao e respostas gerais.";
  }

  if (provider === "openai") {
    if (model.includes("mini")) return "Mais barato e rapido. Bom para classificacao, agentes simples e automacao.";
    if (model.includes("gpt-4") || model.includes("gpt-5")) return "Modelo forte para conversa, raciocinio e respostas mais confiaveis.";
    if (model.includes("embedding")) return "Modelo de embedding da OpenAI. Use para busca semantica/memoria, nao para chat.";
    if (model.includes("transcribe") || model.includes("tts")) return "Modelo de audio. Use em fluxos de voz, nao como LLM principal.";
    return "Modelo OpenAI online. Boa opcao geral para qualidade e ferramentas.";
  }

  if (provider === "claude") {
    if (model.includes("haiku")) return "Rapido e economico. Bom para classificacao e respostas simples.";
    if (model.includes("sonnet")) return "Equilibrio forte entre qualidade, velocidade e custo. Boa escolha padrao.";
    if (model.includes("opus")) return "Mais potente para raciocinio dificil, com custo/latencia maiores.";
    return "Modelo Claude online. Bom para texto longo, analise e conversa cuidadosa.";
  }

  return "Modelo disponivel no provedor selecionado.";
}

