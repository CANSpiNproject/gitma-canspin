import json
import os
import string
import subprocess
import re
import pandas as pd
from typing import List, Union, Dict, Tuple
from collections import Counter
from gitma_canspin.text import Text
from gitma_canspin.annotation import Annotation
from gitma_canspin.tag import Tag
from gitma_canspin._export_annotations import to_stanford_tsv, create_basic_token_tsv, create_annotated_token_tsv, create_annotated_tei
from gitma_canspin._vizualize import plot_annotations, plot_scaled_annotations, duplicate_rows


def split_property_dict_to_column(ac_df):
    """
    Creates Pandas DataFrame columns for each property in annotation collection.
    """
    properties_dict = {}

    for index, item in enumerate(ac_df['properties']):
        for key in item:
            if key not in properties_dict:
                prev_list = index * [['nan']]
                prev_list.append(item[key])
                properties_dict[key] = prev_list
            else:
                properties_dict[key].append(item[key])

        for prop in properties_dict:
            if prop not in item:
                properties_dict[prop].append(['nan'])

    for prop in properties_dict:
        ac_df[f'prop:{prop}'] = properties_dict[prop]

    return ac_df.drop(columns='properties')


def most_common_token(
        annotation_col: pd.Series,
        stopwords: list = None,
        ranking: int = 10) -> dict:
    """Counts Token for list of strings.

    Args:
        annotation_col (pd.Series): The columns name to be analyzed.
        stopwords (list, optional): List of stopwords. Defaults to None.
        ranking (int, optional): Number of most common token to include. Defaults to 10.

    Returns:
        dict: Dictionary storing the token freqeuncies.
    """
    token_list = []
    for str_item in annotation_col:
        removed_punctation = str_item.translate(
            str.maketrans('', '', string.punctuation))
        token_list.extend(removed_punctation.split(' '))

    while '' in token_list:
        token_list.remove('')

    # remove stopwords
    if stopwords:
        token_list = [
            token for token in token_list if token not in stopwords]

    return dict(Counter(token_list).most_common(ranking))


def get_text_span_per_tag(ac_df: pd.DataFrame) -> int:
    return sum(ac_df['end_point'] - ac_df['start_point'])


def get_text_span_mean_per_tag(ac_df: pd.DataFrame) -> int:
    return sum(ac_df['end_point'] - ac_df['start_point']) / len(ac_df)


def clean_text_in_ac_df(annotation: str) -> str:
    annotation = re.sub('\n', ' ', annotation)
    annotation = re.sub(' +', ' ', annotation)
    return annotation


def load_annotations(catma_project, ac, context: int):
    base_dir = f'{os.getcwd()}/{catma_project.uuid}/collections/{ac.uuid}/annotations/'
    # load all annotation collection page files
    for filename in os.listdir(base_dir):
        page_file_path = base_dir + filename
        with open(page_file_path, 'r', encoding='utf-8', newline='') as page_file:
            # load all annotations
            page_file_annotations = json.load(page_file)

        # construct Annotation objects
        for annotation_data in page_file_annotations:
            yield Annotation(
                    annotation_data=annotation_data,
                    page_file_path=page_file_path,
                    plain_text=ac.text.plain_text,
                    project=catma_project,
                    context=context
            )


df_columns = [
    'document', 'annotation collection', 'annotator',
    'tag', 'tag_path', 'properties', 'left_context', 'annotation',
    'right_context', 'start_point', 'end_point', 'date'
]


def ac_to_df(annotations: List[Annotation], text_title, ac_name) -> pd.DataFrame:
    # create df
    df = pd.DataFrame(
        [
            (
                text_title, ac_name, a.author, a.tag.name, a.tag.full_path,
                a.properties, a.pretext, a.text, a.posttext, a.start_point,
                a.end_point, a.date
            ) for a in annotations
        ], columns=df_columns
    )

    # create property columns
    df = split_property_dict_to_column(df)

    # clean annotations
    df['left_context'] = df['left_context'].apply(clean_text_in_ac_df)
    df['annotation'] = df['annotation'].apply(clean_text_in_ac_df)
    df['right_context'] = df['right_context'].apply(clean_text_in_ac_df)

    return df


class AnnotationCollection:
    """Class which represents a CATMA annotation collection.

    Args:
        ac_uuid (str): The annotation collection's UUID
        catma_project (CatmaProject): The parent CatmaProject
        context (int, optional): The text span to be considered for the annotation context. Defaults to 50.

    Raises:
        FileNotFoundError: If the path of the annotation collection's header.json does not exist.
    """

    def __init__(self, ac_uuid: str, catma_project, context: int = 50):
        #: The annotation collection's UUID.
        self.uuid: str = ac_uuid

        #: The directory where the parent project is located.
        self.projects_directory: str = catma_project.projects_directory

        #: The parent project's UUID.
        self.project_uuid: str = catma_project.uuid

        #: The annotation collection's directory.
        self.directory: str = f'{catma_project.uuid}/collections/{self.uuid}/'

        try:
            with open(self.directory + 'header.json', 'r', encoding='utf-8', newline='') as header_json:
                self.header: str = json.load(header_json)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"The annotation collection at this path could not be found: {self.directory}\n\
                    --> Make sure the CATMA project clone worked properly.")

        #: The annotation collection's name.
        self.name: str = self.header['name']

        #: The UUID of the annotation collection's document.
        self.plain_text_id: str = self.header['sourceDocumentId']

        #: The document of the annotation collection as a gitma_canspin.Text object.
        self.text: Text = Text(
            project_uuid=catma_project.uuid,
            document_uuid=self.plain_text_id
        )

        #: The document's version.
        self.text_version: str = self.header.get('sourceDocumentVersion')

        if os.path.isdir(self.directory + 'annotations/'):
            #: List of annotations in annotation collection as gitma_canspin.Annotation objects.
            self.annotations: List[Annotation] = sorted(list(load_annotations(
                catma_project=catma_project,
                ac=self,
                context=context
            )))

            #: List of tags found in the annotation collection as a list of gitma_canspin.Tag objects.
            self.tags: List[Tag] = [an.tag for an in self.annotations]

            #:  Annotations as a pandas.DataFrame.
            self.df: pd.DataFrame = ac_to_df(
                annotations=self.annotations,
                text_title=self.text.title,
                ac_name=self.name
            )
        else:
            self.annotations: list = []
            self.df: pd.DataFrame = pd.DataFrame(columns=df_columns)

    def __repr__(self):
        return f"AnnotationCollection(Name: {self.name}, Document: {self.text.title}, Length: {len(self)})"

    def __len__(self):
        return len(self.annotations)

    def __iter__(self):
        for an in self.annotations:
            yield an

    def to_list(self, tags: Union[list, None] = None) -> List[dict]:
        """Returns list of annotations as dictionaries using the `Annotation.to_dict()` method.

        Args:
            tags(Union[list, None]): Tags included in the annotations list. If `None` all tags are included. Defaults to None.

        Returns:
            List[dict]: List of annotations as dictionaries.
        """
        if not tags:
            tags = self.df.tag.unique()
        
        return [
            an.to_dict() for an in self.annotations
            if an.tag.name in tags
        ]
    
    def annotation_dict(self) -> Dict[str, Annotation]:
        """Creates dictionary with UUIDs as keys an Annotation objects as values.

        Returns:
            Dict[str, Annotation]: Dictionary with UUIDs as keys an Annotation objects as values.
        """
        return {an.uuid: an for an in self.annotations}

    def duplicate_by_prop(self, prop: str) -> pd.DataFrame:
        """Duplicates the rows in the annotation collection's DataFrame if the given Property has multiple Property Values
        the annotations represented by a DataFrame row.

        Args:
            prop (str): A property used in the annotation collection.

        Raises:
            ValueError: If the property has not been used in the annotation collection.

        Returns:
            pd.DataFrame: A duplicate of the annotation collection's DataFrame.
        """
        try:
            return duplicate_rows(ac_df=self.df, property_col=prop)
        except KeyError:
            prop_cols = [item.replace('prop:', '')
                         for item in self.df.columns if 'prop:' in item]
            raise ValueError(
                f"Given Property doesn't exist. Choose one of these: {prop_cols}")

    def push_annotations(self, commit_message: str = 'new annotations') -> None:
        """Process `git add .`, `git commit` and `git push` for a single annotation collection.

        *Note*: Works only if git is installed and the CATMA access token is stored in the **git
        credential manager**.

        Args:
            commit_message (str, optional): Customize the commit message. Defaults to 'new annotations'.
        """
        cwd = os.getcwd()
        os.chdir(f'{self.projects_directory}{self.directory}')
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', commit_message])
        subprocess.run(['git', 'push', 'origin', 'master'])
        os.chdir(cwd)
        print(f'Pushed annotations from collection {self.name}.')
    
    def plot_annotations(self, y_axis: str = 'tag', color_prop: str = 'tag'):
        """Creates interactive [Plotly Scatter Plot](https://plotly.com/python/line-and-scatter/) to a explore a annotation collection.

        Args:
            y_axis (str, optional): The columns in AnnotationCollection DataFrame used for y axis. Defaults to 'tag'.
            color_prop (str, optional): A Property's name used in the AnnotationCollection . Defaults to None.

        Returns:
            go.Figure: Plotly scatter plot.
        """
        return plot_annotations(ac=self, y_axis=y_axis, color_prop=color_prop)

    def filter_by_tag_path(self, path_element: str) -> pd.DataFrame:
        """Filters annotation collection data frame for annations with the given `path_element` in the tag's full path.

        Args:
            path_element (str): Any tag name with the used tagsets.

        Returns:
            pd.DataFrame: Data frame in the format of the annotation collection data frames.
        """
        return self.df[self.df.tag_path.str.contains(path_element)]
    
    def plot_scaled_annotations(
            self,
            tag_scale: dict = None,
            bin_size: int = 50,
            smoothing_window: int = 100):
        """Plots a graph with scaled annotations.
        This function is still under development.

        Args:
            tag_scale (dict, optional): _description_. Defaults to None.
            bin_size (int, optional): _description_. Defaults to 50.
            smoothing_window (int, optional): _description_. Defaults to 100.

        Raises:
            Exception: _description_
        """
        return plot_scaled_annotations(ac=self, tag_scale=tag_scale, bin_size=bin_size, smoothing_window=smoothing_window)

    def cooccurrence_network(
            self,
            character_distance: int = 100,
            included_tags: list = None, excluded_tags: list = None,
            level: str = 'tag',
            plot_stats: bool = False,
            save_as_gexf: Union[bool, str]= False):
        """Draws cooccurrence network graph where every tag is a node and every edge represents two cooccurent tags.
        You can by the `character_distance` parameter when two annotations are considered cooccurent.
        If you set `character_distance=0` only the tags of overlapping annotations will be represented
        as connected nodes.

        Args:
            character_distance (int, optional): In which distance annotations are considered coocurrent. Defaults to 100.
            included_tags (list, optional): List of included tags. Defaults to None.
            level (str, optional): Select 'tag' or any property in your annotation collections with the prefix 'prop'.
            excluded_tags (list, optional): List of excluded tags. Defaults to None.
            plot_stats (bool, optional): Whether to return network stats. Defaults to False.
            save_as_gexf (bool, optional): If given any string as filename the network gets saved as Gephi file.
        """
        from gitma_canspin._network import Network

        nw = Network(
            annotation_collections=[self],
            character_distance=character_distance,
            included_tags=included_tags,
            excluded_tags=excluded_tags,
            level=level
        )
        if save_as_gexf:
            nw.to_gexf(filename=save_as_gexf)

        return nw.plot(plot_stats=plot_stats)

    def to_pygamma_table(self) -> pd.DataFrame:
        """Returns the annotation collection's DataFrame in the format pygamma takes as input.

        Returns:
            pd.DataFrame: DataFrame with four columns: 'annotator', 'tag', 'start_point' and 'end_point'.
        """
        return self.df[['annotator', 'tag', 'start_point', 'end_point']]

    def tag_stats(
            self,
            tag_col: str = 'tag',
            stopwords: list = None,
            ranking: int = 10) -> pd.DataFrame:
        """Computes the following data for each tag in the annotation collection:
        - the count of annotations with a tag
        - the complete text span annotated with a tag
        - the average text span annotated with a tag
        - the n-most frequent token in the text span annotated with a tag

        Args:
            tag_col (str, optional): Whether the data for the tag a property or annotators gets computed. Defaults to 'tag'.
            stopwords (list, optional): A list with stopword tokens. Defaults to None.
            ranking (int, optional): The number of most frequent token to be included. Defaults to 10.

        Returns:
            pd.DataFrame: The data as pandas DataFrame.
        """

        if 'prop:' in tag_col:
            analyze_df = duplicate_rows(self.df, property_col=tag_col)
        else:
            analyze_df = self.df

        tag_data = {}
        for tag in analyze_df[tag_col].unique():
            filtered_df = analyze_df[analyze_df[tag_col] == tag]
            tag_data[tag] = {
                'annotations': len(filtered_df),
                'text_span': get_text_span_per_tag(ac_df=filtered_df),
                'text_span_mean': get_text_span_mean_per_tag(ac_df=filtered_df),
            }
            mct = most_common_token(
                annotation_col=filtered_df['annotation'],
                stopwords=stopwords,
                ranking=ranking
            )
            for token_index, token in enumerate(mct):
                tag_data[tag][f'token{token_index + 1}'] = f'{token}: {mct[token]}'

        return pd.DataFrame(tag_data).T

    def property_stats(self) -> pd.DataFrame:
        """Counts for each property the property values.

        Returns:
            pd.DataFrame: DataFrame with properties as index and property values as header.
        """
        return pd.DataFrame(
            {col: duplicate_rows(self.df, col)[col].value_counts(
            ) for col in self.df.columns if 'prop:' in col}
        ).T

    def get_annotation_by_tag(self, tag_name: str) -> List[Annotation]:
        """Creates list of all annotations with a given name.

        Args:
            tag_name (str): The searched tag's name.

        Returns:
            List[Annotation]: List of annotations as gitma_canspin.Annotation objects.
        """
        return [
            annotation for annotation in self.annotations
            if annotation.tag.name == tag_name
            or annotation.tag.parent.name == tag_name
        ]

    def annotate_properties(self, tag: str, prop: str, value: list):
        """Set value for given property. This function uses the `gitma_canspin.Annotation.set_property_values()` method.

        Args:
            tag (str): The parent tag of the property.
            prop (str): The property to be annotated.
            value (list): The new property value.
        """
        for an in self.annotations:
            an.set_property_values(tag=tag, prop=prop, value=value)

    def rename_property_value(self, tag: str, prop: str, old_value: str, new_value: str):
        """Renames Property of all annotations with the given tag name.
        Replaces only the property value defined by the parameter `old_value`.

        Args:
            tag (str): The tag's name-
            prop (str): The property's name-
            old_value (str): The old property value that will be replaced.
            new_value (str): The new property value that will replace the old property value.
        """
        for an in self.annotations:
            an.modify_property_value(
                tag=tag, prop=prop, old_value=old_value, new_value=new_value)

    def delete_properties(self, tag: str, prop: str):
        """Deletes a property from all annotations with a given tag name.

        Args:
            tag (str): The annotations tag name.
            prop (str): The name of the property that will be removed.
        """
        for an in self.annotations:
            an.delete_property(tag=tag, prop=prop)

    def to_stanford_tsv(
        self,
        tags: Union[list, str] = 'all',
        file_name: str = 'tsv_annotation_export',
        spacy_model_lang: str = 'German'):
        """Takes a CATMA `AnnotationCollection` and writes a tsv file which can be used to train a stanford NER model.
        Every token in the collection's text gets a tag if it lays in an annotated text segment. 

        Args:
            tags (Union[list, str], optional): List of tags, that should be considered. If set to 'all' all annotations are included.\
                Defaults to 'all'.
            file_name (str, optional): name of the tsv-file. Defaults to 'tsv_annotation_export'.
            spacy_model_lang (str, optional): a spacy model selected by language ('German', 'English', 'Multilingual', 'French', 'Spanish'). Defaults to 'German'.
        """
        if tags == 'all':
            tags = list(self.df['tag'].unique())
        to_stanford_tsv(ac=self, tags=tags, file_name=file_name, spacy_model_lang=spacy_model_lang)

    def create_basic_token_tsv(
        self,
        created_file_name: str = 'basic_token_table',
        spacy_model_lang: str = 'German',
        text_borders: Union[Tuple[int, int], None] = None,
        nlp_max_text_len: Union[int, None] = None):
        """Takes a CATMA `AnnotationCollection`, writes a basic token tsv file with Token_ID, Text_Pointer and Token columns.
        
        Args:
            created_file_name (str): name of the tsv file to be created. Defaults to 'basic_token_table'.
            spacy_model_lang (str, optional): a spacy model selected by language ('German', 'English', 'Multilingual', 'French', 'Spanish'). Defaults to 'German'.
            text_borders (tuple, optional): cut off delivered text by begin and end value of text string.
            nlp_max_text_len (int, optional): specifies spacys accepted max text length for tokenization.
        """
        create_basic_token_tsv(ac=self, created_file_name=created_file_name, spacy_model_lang=spacy_model_lang, text_borders=text_borders, nlp_max_text_len=nlp_max_text_len)
    
    def create_annotated_token_tsv(
        self,
        basic_token_file_name: str = 'basic_token_table',
        created_file_name: str = 'annotated_token_table',
        text_borders: Union[Tuple[int, int], None] = None,
        use_all_text_selection_segments: bool = True):
        """Takes a CATMA `AnnotationCollection`, writes a annotated token tsv file with Token_ID, Text_Pointer, Token, Tag, Annotation_ID and Multi_Token_Annotation columns.
        
        Args:
            basic_token_file_name (str): name of existing basic token tsv file.
            created_file_name (str): name of the tsv file to be created. Defaults to 'annotated_token_table'.
            text_borders (tuple, optional): cut off delivered text by begin and end value of text string. It must have the same value as it had when creating the delivered basic token tsv file.
            use_all_text_selection_segments (bool, optional): the parameter sets the processing mode for text selection segments. There are two processing modes: Consider all text selection segments of an annotation for the export (True: used for short, discontinuous annotations) or consider only the start and end point of an annotation and treat this as a single text selection segment, even if several segments are present in the data (False: used for longer, contiguous annotations). This mode distinction is necessary because CATMA divides longer, contiguous annotations internally into several text selection segments and this division should not be passed on to the exported data.
        """
        create_annotated_token_tsv(ac=self, basic_token_file_name=basic_token_file_name, created_file_name=created_file_name, text_borders=text_borders, use_all_text_selection_segments=use_all_text_selection_segments)

    def create_annotated_tei(
        self,
        annotated_token_file_name: str = 'annotated_token_table',
        created_file_name: str = 'annotated_tei',
        insert_paragraphs: bool = True,
        paragraph_recognition_text_class: str = 'eltec-deu'):
        """Takes an annotated token tsv file with Token_ID, Text_Pointer, Token, Tag, Annotation_ID and Multi_Token_Annotation columns and writes a tei xml file.
        
        Args:
            annotated_token_file_name (str): name of existing annotated token tsv file. Defaults to 'annotated_token_table'.
            created_file_name (str): name of the tei xml file. Defaults to 'annotated_tei'.
            insert_paragraphs (bool): controls if file text is put directly into body element or in childen-p elements, if paragraphs were delivered originally when the text was imported into CATMA. Defaults to True.
            paragraph_recognition_text_class (str): selects a condition against which token are checked against in xml creation process to decide where a new paragraph begins. Defaults to 'eltec-deu'.
        """
        create_annotated_tei(annotated_token_file_name=annotated_token_file_name, created_file_name=created_file_name, insert_paragraphs=insert_paragraphs, paragraph_recognition_text_class=paragraph_recognition_text_class)

    def write_annotation_csv(
        self,
        tags: Union[str, list] = 'all',
        property: str = 'all',
        only_missing_prop_values: bool = False,
        filename: str = 'PropertyAnnotationTable'):
        """Creates csv file to add propertiy values to existing annotations.
        The added property values can be imported with the `read_annotation_csv()` method.

        [See the example below.](
            https://gitma.readthedocs.io/en/latest/class_annotation_collection.html#add-property-values-via-csv-table
        )


        Args:
            tags (Union[str, list], optional): List of tag names to be included.\
                If set to 'all' all annotations will be written into the csv file.\
                Defaults to 'all'.
            property (str, optional): The property to be included.\
                If set to 'all' all annotations will be written into the csv file.\
                Defaults to 'all'.
            only_missing_prop_values (bool, optional): Whether only empy properties should be included.\
                Defaults to False.
            filename (str, optional): The csv file name. Defaults to 'PropertyAnnotationTable'.
        """
        
        # filter annotations by selected tags
        if tags == 'all':
            annotations = self.annotations
        else:
            annotations = [an for an in self.annotations if an.tag.name in tags]
        
        # get list of properties to be modified
        if property == 'all':
            # use the annotation collection's data frame to collect all used properties
            properties = [col for col in self.df.columns if 'prop:' in col]
            properties = [prop.replace('prop:', '') for prop in properties]
        else:
            properties = [property]
        
        # list with annotations that get annotated
        annotation_output = []
        for an in annotations:
            for prop in an.properties:
                if prop in properties:
                    if only_missing_prop_values:
                        if len(an.properties[prop]) < 1:
                            annotation_output.append(
                                {
                                    'id': an.uuid,
                                    'annotation_collection': self.name,
                                    'tag': an.tag.name,
                                    'text': clean_text_in_ac_df(an.text),
                                    'property': prop,
                                    'values': ''
                                }
                            )
                    else:
                        annotation_output.append(
                            {
                                'id': an.uuid,
                                'annotation_collection': self.name,
                                'text': clean_text_in_ac_df(an.text),
                                'tag': an.tag.name,
                                'property': prop,
                                'values': ','.join(an.properties[prop])
                            }
                        )
        annotation_df = pd.DataFrame(annotation_output)
        annotation_df.to_csv(f'{filename}.csv', encoding='utf-8', index=None, sep=";")

    def read_annotation_csv(
        self,
        filename: str = 'PropertyAnnotationTable.csv',
        push_to_gitlab=False) -> None:
        """Reads csv file created by the `write_annotation_csv()` method and updates
        the annotation json files. Additionally, if `push_to_gitlab=True` the annotations
        get imported in the CATMA Gitlab backend.
        
        [See the example below.](https://gitma.readthedocs.io/en/latest/class_annotation_collection.html#add-property-values-via-csv-table)

        Args:
            filename (str, optional): The annotation csv file's name/directory.\
                Defaults to 'PropertyAnnotationTable.csv'.
            push_to_gitlab (bool, optional): Whether to push the annotations to gitlab. Defaults to False.
        """
        annotation_table = pd.read_csv(filename, sep=";")
        an_dict = self.annotation_dict()

        
        cwd = os.getcwd()
        os.chdir(self.projects_directory)
        annotation_counter = 0
        missed_annotation_counter = 0
        for _, row in annotation_table.iterrows():
            try:
                if isinstance(row['values'], str):    # test if any property values are defined
                    an_dict[row['id']].set_property_values(
                        tag=row['tag'],
                        prop=row['property'],
                        value=row['values'].split(',')
                    )
                    annotation_counter += 1
                else:
                    missed_annotation_counter += 1
            except KeyError:
                missed_annotation_counter += 1
        
        if push_to_gitlab:
            os.chdir(self.directory)
            subprocess.run(['git', 'add', '.'])
            subprocess.run(['git', 'commit', '-m', 'new property annotations'])
            subprocess.run(['git', 'push', 'origin', 'HEAD:master'])
        os.chdir(cwd)
        print(f"Updated values for {annotation_counter} annotations.")
        if not push_to_gitlab:
            print(f'Your annotations are stored in {self.directory}')
