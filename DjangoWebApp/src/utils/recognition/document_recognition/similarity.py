from utils.recognition.document_recognition.regex import Regex
import numpy as np

class StringSimilarity:
    @staticmethod
    def levenshtein_distance(s1,s2,check_compatible=False):
        num_cols = len(s2)+1
        num_rows = len(s1)+1

        tab = [[col if row == 0 else row if col == 0 else None for col in range(num_cols)] for row in range(num_rows)]

        for c1 in range(len(s1)):
            for c2 in range(len(s2)):
                i, j = c1 + 1, c2 + 1
                
                tab[i][j] = min(tab[i-1][j] + 1, # deletion
                                tab[i][j-1] + 1, # insertion
                                tab[i-1][j-1] + (int(s1[c1] != s2[c2]) \
                                                 if not check_compatible \
                                                 else StringSimilarity.__check_compatible_match(s1[c1], s2[c2]))) # substitution or match

        return tab[-1][-1]

    @staticmethod
    def __check_compatible_match(c1, c2):
        if c1 == c2:
            return 0
        
        for match_set in Regex.compatible:
            if c1 in match_set and c2 in match_set:
                return 0
            
        return 1

class VectorSimilarity:
    @staticmethod
    def euclidean_distance(vector1, vector2):
        vector1 = VectorSimilarity.assert_np_array(vector1)
        vector2 = VectorSimilarity.assert_np_array(vector2)
        
        distance_vector = np.square(vector1 - vector2)
        return np.sqrt(distance_vector.sum())
    
    @staticmethod
    def cosine_distance(vector1, vector2):
        vector1 = VectorSimilarity.assert_np_array(vector1)
        vector2 = VectorSimilarity.assert_np_array(vector2)
        
        a = np.matmul(np.transpose(vector1), vector2)
        b = np.matmul(np.transpose(vector1), vector1)
        c = np.matmul(np.transpose(vector2), vector2)

        return 1 - (a / (np.sqrt(b) * np.sqrt(c)))
    
    @staticmethod
    def assert_np_array(vector):
        if not isinstance(vector, list):
            if isinstance(vector, str):
                vector = np.fromstring(vector[1:-1], dtype=np.float, sep=' ')
            else:
                vector = np.array(vector)
            
        assert isinstance(vector, np.ndarray), "Vector input should be numpy array."
        return vector

