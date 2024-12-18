import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os

TASKS_FILE = "tasks.csv"

def init_csv():
    if not os.path.exists(TASKS_FILE):
        df = pd.DataFrame(columns=[
            'id', 'date', 'scheduled_time', 'description', 
            'priority', 'status', 'category'
        ])
        df.to_csv(TASKS_FILE, index=False)

def get_next_id():
    df = pd.read_csv(TASKS_FILE)
    return 1 if df.empty else df['id'].max() + 1

def add_task(date, scheduled_time, description, priority, category, status="Pendente"):
    df = pd.read_csv(TASKS_FILE)
    new_task = pd.DataFrame([{
        'id': get_next_id(),
        'date': date,
        'scheduled_time': scheduled_time,
        'description': description,
        'priority': priority,
        'status': status,
        'category': category
    }])
    df = pd.concat([df, new_task], ignore_index=True)
    df.to_csv(TASKS_FILE, index=False)

def get_tasks(date=None):
    df = pd.read_csv(TASKS_FILE)
    if date and not df.empty:
        df = df[df['date'] == date]
        df = df.sort_values('scheduled_time')
    return df

def delete_task(task_id):
    df = pd.read_csv(TASKS_FILE)
    df = df[df['id'] != task_id]
    df.to_csv(TASKS_FILE, index=False)

def update_task_status(task_id, new_status):
    df = pd.read_csv(TASKS_FILE)
    df.loc[df['id'] == task_id, 'status'] = new_status
    df.to_csv(TASKS_FILE, index=False)

def get_weekly_stats():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    df = pd.read_csv(TASKS_FILE)
    if not df.empty:
        mask = (pd.to_datetime(df['date']) >= start_date.strftime("%Y-%m-%d")) & \
               (pd.to_datetime(df['date']) <= end_date.strftime("%Y-%m-%d"))
        return df[mask].groupby(['date', 'status']).size().reset_index(name='count')
    return pd.DataFrame()

def main():
    st.title("Planejamento Diário")
    init_csv()

    st.sidebar.header("Menu")
    page = st.sidebar.selectbox("Escolha uma opção", 
                              ["Adicionar Tarefa", "Visualizar Tarefas", "Dashboard", "Resumo Semanal"])

    if page == "Adicionar Tarefa":
        st.subheader("Nova Tarefa")
        
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Data", datetime.now())
        with col2:
            scheduled_time = st.time_input("Horário Planejado", datetime.now().time())
            
        description = st.text_area("Descrição da Tarefa")
        priority = st.selectbox("Prioridade", ["Alta", "Média", "Baixa"])
        category = st.selectbox("Categoria", ["Trabalho", "Pessoal", "Estudo", "Saúde"])
        
        if st.button("Adicionar"):
            add_task(
                date.strftime("%Y-%m-%d"),
                scheduled_time.strftime("%H:%M"),
                description,
                priority,
                category
            )
            st.success("Tarefa adicionada com sucesso!")

    elif page == "Dashboard":
        st.subheader("Dashboard de Tarefas")
        
        all_tasks = get_tasks()
        if not all_tasks.empty:
            status_counts = all_tasks['status'].value_counts()
            fig = px.pie(values=status_counts.values, 
                        names=status_counts.index, 
                        title='Distribuição de Status das Tarefas')
            st.plotly_chart(fig)
            
            category_status = pd.crosstab(all_tasks['category'], all_tasks['status'])
            fig2 = px.bar(category_status, 
                         title='Status por Categoria',
                         barmode='group')
            st.plotly_chart(fig2)
        else:
            st.warning("Sem tarefas registradas no sistema")

    elif page == "Resumo Semanal":
        st.subheader("Resumo Semanal")
        
        weekly_stats = get_weekly_stats()
        if not weekly_stats.empty:
            fig = px.line(weekly_stats, 
                         x='date', 
                         y='count', 
                         color='status',
                         title='Progresso Semanal')
            st.plotly_chart(fig)
            
            completed_tasks = weekly_stats[weekly_stats['status'] == 'Concluída']['count'].sum()
            st.metric("Total de Tarefas Concluídas", completed_tasks)
        else:
            st.warning("Sem tarefas registradas para a última semana")

    else:  # Visualizar Tarefas
        st.subheader("Minhas Tarefas")
        
        filter_date = st.date_input("Filtrar por data", datetime.now())
        tasks = get_tasks(filter_date.strftime("%Y-%m-%d"))
        
        if not tasks.empty:
            for idx, task in tasks.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{task['scheduled_time']} - {task['description']}**")
                    st.write(f"Prioridade: {task['priority']} | Categoria: {task['category']}")
                
                with col2:
                    current_status = task['status']
                    new_status = st.selectbox(
                        "Status",
                        ["Pendente", "Em Andamento", "Concluída"],
                        index=["Pendente", "Em Andamento", "Concluída"].index(current_status),
                        key=f"status_{task['id']}"
                    )
                    
                    if new_status != current_status:
                        update_task_status(task['id'], new_status)
                        st.experimental_rerun()
                
                with col3:
                    if task['status'] != "Pendente":
                        if st.button("Excluir", key=f"del_{task['id']}"):
                            delete_task(task['id'])
                            st.experimental_rerun()
                
                st.divider()
        else:
            st.warning("Sem tarefas para o período")

if __name__ == "__main__":
    main()
